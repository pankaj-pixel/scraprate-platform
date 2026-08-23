const HELP_TEXT = 'Confidence reflects the number and quality of active price sources.';

export default function ConfidenceBadge({ level = 'LOW' }) {
  const normalized = String(level).toLowerCase();
  return (
    <span
      className={`confidence-badge confidence-badge--${normalized}`}
      title={HELP_TEXT}
      aria-label={`${level} confidence. ${HELP_TEXT}`}
      tabIndex="0"
    >
      {level} confidence
    </span>
  );
}
