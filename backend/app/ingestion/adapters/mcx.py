import csv
import io
import zipfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from app.config import get_settings
from app.ingestion.adapters.base import AdapterObservation, PriceSourceAdapter

MCX_SOURCE_SLUG = "mcx-bhavcopy"
MCX_MATERIAL_MAP = {"COPPER": "copper", "ALUMINIUM": "aluminium"}
DATE_FORMATS = ("%d-%b-%Y", "%d%b%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y")

class McxPayloadError(ValueError): pass

def map_commodity(symbol: str) -> str:
    try: return MCX_MATERIAL_MAP[symbol.strip().upper()]
    except KeyError as exc: raise McxPayloadError(f"Unsupported MCX commodity: {symbol}") from exc

def _field(row, *names, required=True):
    lookup={str(k).strip().upper():v for k,v in row.items()}
    for name in names:
        value=lookup.get(name.upper())
        if value is not None and str(value).strip() not in {"","-"}: return str(value).strip()
    if required: raise McxPayloadError(f"Missing required MCX field: {names[0]}")
    return None

def _date(value: str) -> date:
    for pattern in DATE_FORMATS:
        try: return datetime.strptime(value.strip(),pattern).date()
        except ValueError: pass
    raise McxPayloadError(f"Invalid MCX date: {value}")

def _decimal(value: str, field: str) -> Decimal:
    try: result=Decimal(value.replace(",",""))
    except (InvalidOperation,AttributeError) as exc: raise McxPayloadError(f"Invalid MCX {field}") from exc
    if not result.is_finite() or result <= 0: raise McxPayloadError(f"Invalid MCX {field}")
    return result

class McxBhavcopyAdapter(PriceSourceAdapter):
    """Official MCX contract-level EOD Bhavcopy CSV/ZIP adapter.

    The URL is intentionally configuration-only because MCX does not publish a
    stable unauthenticated download API contract. Only official mcxindia.com
    download URLs are accepted.
    """
    @property
    def source_identifier(self): return MCX_SOURCE_SLUG

    def fetch(self) -> bytes:
        url=get_settings().mcx_bhavcopy_url
        if not url: raise McxPayloadError("MCX_BHAVCOPY_URL is not configured")
        parsed=urlparse(url)
        if parsed.scheme != "https" or not (parsed.hostname=="mcxindia.com" or parsed.hostname.endswith(".mcxindia.com")):
            raise McxPayloadError("MCX Bhavcopy URL must use HTTPS on an official mcxindia.com host")
        try:
            with urlopen(Request(url,headers={"User-Agent":"ScrapRate-MCX-Benchmark/1.0"}),timeout=30) as response: return response.read()
        except Exception as exc: raise McxPayloadError(f"MCX Bhavcopy unavailable: {exc}") from exc

    def parse(self, raw: bytes) -> list[dict[str,str]]:
        if not raw: raise McxPayloadError("MCX Bhavcopy is empty")
        if raw[:2]==b"PK":
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    names=[x for x in archive.namelist() if x.lower().endswith(".csv")]
                    if len(names)!=1: raise McxPayloadError("MCX ZIP must contain exactly one CSV file")
                    raw=archive.read(names[0])
            except zipfile.BadZipFile as exc: raise McxPayloadError("Malformed MCX ZIP payload") from exc
        try: text=raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc: raise McxPayloadError("MCX Bhavcopy must be UTF-8 CSV") from exc
        reader=csv.DictReader(io.StringIO(text))
        if not reader.fieldnames: raise McxPayloadError("MCX Bhavcopy has no header")
        required={x.upper() for x in reader.fieldnames}
        if not ({"SYMBOL","COMMODITY"}&required) or not ({"CLOSE","CLOSINGPRICE","CLOSE_PRICE"}&required):
            raise McxPayloadError("Malformed MCX Bhavcopy header")
        rows=list(reader)
        if not rows: raise McxPayloadError("MCX Bhavcopy contains no records")
        return rows

    def normalize(self, rows: list[dict[str,str]]) -> list[AdapterObservation]:
        candidates={}
        for row in rows:
            instrument=(_field(row,"INSTRUMENT","INSTRUMENTNAME",required=False) or "FUTCOM").upper()
            if instrument not in {"FUTCOM","FUTURES"}: continue
            symbol=_field(row,"SYMBOL","COMMODITY").upper()
            if symbol not in MCX_MATERIAL_MAP: continue
            trading_date=_date(_field(row,"TIMESTAMP","TRADE_DATE","TRADINGDATE"))
            expiry=_date(_field(row,"EXPIRY_DT","EXPIRYDATE","EXPIRY"))
            if expiry < trading_date: continue
            candidates.setdefault((symbol,trading_date),[]).append((expiry,row))
        if not candidates: raise McxPayloadError("Bhavcopy has no supported active COPPER or ALUMINIUM futures contracts")
        output=[]
        for (symbol,trading_date),contracts in sorted(candidates.items()):
            expiry,row=min(contracts,key=lambda item:item[0])
            open_price=_decimal(_field(row,"OPEN","OPENPRICE"),"open")
            high=_decimal(_field(row,"HIGH","HIGHPRICE"),"high")
            low=_decimal(_field(row,"LOW","LOWPRICE"),"low")
            close=_decimal(_field(row,"CLOSE","CLOSINGPRICE","CLOSE_PRICE"),"close")
            previous=_field(row,"PREV_CLOSE","PREVIOUSCLOSE","PREVCLOSE",required=False)
            source_url=get_settings().mcx_bhavcopy_url
            output.append(AdapterObservation(source=MCX_SOURCE_SLUG,material=map_commodity(symbol),city=None,date=trading_date,
                low_price=low,average_price=close,high_price=high,unit="kg",raw_reference=source_url,
                metadata={"benchmark":True,"mcx_commodity":symbol,"contract":f"{symbol}-{expiry.isoformat()}","expiry":expiry.isoformat(),
                    "trading_date":trading_date.isoformat(),"open":str(open_price),"high":str(high),"low":str(low),"close":str(close),
                    "previous_close":str(_decimal(previous,"previous close")) if previous else None,"source_url":source_url},price_context="benchmark"))
        return output
