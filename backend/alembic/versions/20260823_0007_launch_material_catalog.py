"""Expand the soft-launch material catalog without replacing existing IDs.

Revision ID: 20260823_0007
Revises: 20260822_0006
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "20260823_0007"
down_revision: str | None = "20260822_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_MATERIALS = [
    ("light-iron","Light Iron","metal","FeL","Light-gauge iron sheet and low-density ferrous scrap.",7,["light iron"],"Light Iron Scrap Price Today in Delhi NCR"),
    ("steel","Steel","metal","St","General steel scrap published without a stainless grade claim.",8,["steel scrap"],"Steel Scrap Price Today in Delhi NCR"),
    ("tin-light-iron","Tin Light Iron","metal","TLI","Thin tin-coated or light ferrous sheet scrap.",9,["tin light iron"],"Tin Light Iron Scrap Price Today"),
    ("motor-copper-wiring","Motor Copper Wiring","metal","MCW","Mixed motor scrap containing recoverable copper winding.",10,["motor copper wiring"],"Motor Copper Wiring Scrap Rate Today"),
    ("stabilizer-copper","Stabilizer Copper Scrap","metal","SC","Stabilizer scrap valued for recoverable copper content.",11,["stabilizer copper"],"Stabilizer Copper Scrap Rate Today"),
    ("fan-copper-wiring","Fan Copper Wiring","metal","FCW","Fan motor scrap containing copper winding.",12,["fan copper wiring"],"Fan Copper Wiring Scrap Rate Today"),
    ("old-books","Old Books","paper","BK","Used books collected as recyclable paper scrap.",21,["books","old book"],"Old Books Scrap Price Today in Delhi NCR"),
    ("magazine","Magazine","paper","MG","Clean used magazines and coated printed paper.",22,["magazines"],"Magazine Scrap Price Today in Delhi NCR"),
    ("office-paper","Office Paper","paper","OP","Clean sorted office paper suitable for recycling.",23,["office paper"],"Office Paper Scrap Price Today"),
    ("plastic","Mixed Plastic","plastic","PL","Generic mixed plastic published without a PET grade claim.",31,["plastic","mixed plastic"],"Mixed Plastic Scrap Price Today in Delhi NCR"),
    ("metal-e-waste","Metal E-Waste","electronics","MEW","Metal-rich mixed electronic scrap; composition affects final value.",41,["metal e-waste"],"Metal E-Waste Scrap Price Today"),
    ("plastic-e-waste","Plastic E-Waste","electronics","PEW","Plastic-rich electronic scrap kept separate from PET packaging.",42,["plastic e-waste"],"Plastic E-Waste Scrap Price Today"),
    ("lcd-tv","LCD TV Scrap","electronics","LTV","LCD television scrap priced by weight when accepted by the source.",43,["lcd tv"],"LCD TV Scrap Price Today in Delhi NCR"),
    ("lcd-monitor","LCD Monitor Scrap","electronics","LM","LCD computer monitor scrap priced by weight.",44,["lcd monitor"],"LCD Monitor Scrap Price Today"),
    ("printer","Printer Scrap","electronics","PR","Mixed printer scrap priced by weight.",45,["printer"],"Printer Scrap Price Today in Delhi NCR"),
    ("white-battery","White Battery","batteries","WB","Source-defined white battery scrap; chemistry and condition require inspection.",51,["white battery"],"White Battery Scrap Price Today"),
    ("black-battery","Black Battery","batteries","BB","Source-defined black battery scrap; chemistry and condition require inspection.",52,["black battery"],"Black Battery Scrap Price Today"),
    ("iron-cooler","Iron Cooler Scrap","appliances","IC","Iron-bodied cooler scrap sold by weight.",61,["iron cooler"],"Iron Cooler Scrap Price Today"),
    ("plastic-cooler","Plastic Cooler Scrap","appliances","PC","Plastic-bodied cooler scrap kept separate from PET plastic.",62,["plastic cooler"],"Plastic Cooler Scrap Price Today"),
    ("inverter-scrap","Inverter Scrap","appliances","INV","Mixed inverter equipment scrap published by weight.",63,["invertor","inverter"],"Inverter Scrap Price Today in Delhi NCR"),
    ("ro-scrap","RO Purifier Scrap","appliances","RO","Mixed reverse-osmosis purifier scrap published by weight.",64,["r.o","ro"],"RO Purifier Scrap Price Today"),
    ("chimney-scrap","Chimney Scrap","appliances","CH","Mixed kitchen chimney scrap published by weight.",65,["chimney"],"Chimney Scrap Price Today"),
    ("glass","Glass Scrap","other-recyclables","GL","Clean recyclable glass published as a weight-based scrap item.",71,["glass"],"Glass Scrap Price Today in Delhi NCR"),
]

def upgrade() -> None:
    op.add_column("materials",sa.Column("seo_title",sa.String(180)))
    op.add_column("materials",sa.Column("seo_description",sa.String(320)))
    op.add_column("materials",sa.Column("display_order",sa.Integer(),server_default="100",nullable=False))
    op.add_column("materials",sa.Column("image_reference",sa.String(255)))
    op.add_column("materials",sa.Column("aliases",sa.JSON()))
    op.add_column("materials",sa.Column("source_material_mapping",sa.JSON()))
    conn=op.get_bind()
    categories={slug:id for id,slug in conn.execute(sa.text("SELECT id, slug FROM material_categories"))}
    additions=[("batteries","Batteries"),("appliances","Appliances"),("other-recyclables","Other Recyclables")]
    for slug,name in additions:
        if slug not in categories:
            conn.execute(sa.text("INSERT INTO material_categories (slug,name) VALUES (:slug,:name)"),{"slug":slug,"name":name})
    conn.execute(sa.text("UPDATE material_categories SET name='Metals' WHERE slug='metal'"))
    conn.execute(sa.text("UPDATE material_categories SET name='E-Waste' WHERE slug='electronics'"))
    categories={slug:id for id,slug in conn.execute(sa.text("SELECT id, slug FROM material_categories"))}
    existing={slug for (slug,) in conn.execute(sa.text("SELECT slug FROM materials"))}
    for slug,name,category,icon,description,order,aliases,title in NEW_MATERIALS:
        if slug in existing: continue
        conn.execute(sa.text("""INSERT INTO materials
          (category_id,slug,name,unit,icon,description,is_active,seo_title,seo_description,display_order,image_reference,aliases,source_material_mapping)
          VALUES (:category_id,:slug,:name,'kg',:icon,:description,true,:title,:seo_description,:display_order,:image_reference,:aliases,:mapping)"""),
          {"category_id":categories[category],"slug":slug,"name":name,"icon":icon,"description":description,"title":title,
           "seo_description":f"Check the latest indicative {name.lower()} price, source freshness and stored price history in Delhi NCR.",
           "display_order":order,"image_reference":f"/materials/{slug}.webp","aliases":sa.text("JSON_ARRAY()") if False else __import__('json').dumps(aliases),
           "mapping":__import__('json').dumps({"urban-scrap":[name.replace(' Scrap','')]})})
    conn.execute(sa.text("UPDATE materials SET seo_title=CONCAT(name, ' Scrap Price Today in Delhi NCR'), seo_description=CONCAT('Check the latest indicative ', LOWER(name), ' price, source freshness and stored trends in Delhi NCR.'), image_reference=CONCAT('/materials/', slug, '.png'), display_order=id WHERE seo_title IS NULL"))

def downgrade() -> None:
    conn=op.get_bind()
    slugs=[row[0] for row in NEW_MATERIALS]
    conn.execute(sa.text("DELETE FROM materials WHERE slug IN :slugs").bindparams(sa.bindparam("slugs",expanding=True)),{"slugs":slugs})
    for slug in ("batteries","appliances","other-recyclables"):
        conn.execute(sa.text("DELETE FROM material_categories WHERE slug=:slug"),{"slug":slug})
    conn.execute(sa.text("UPDATE material_categories SET name='Metal' WHERE slug='metal'")); conn.execute(sa.text("UPDATE material_categories SET name='Electronics' WHERE slug='electronics'"))
    for column in ("source_material_mapping","aliases","image_reference","display_order","seo_description","seo_title"):
        op.drop_column("materials",column)
