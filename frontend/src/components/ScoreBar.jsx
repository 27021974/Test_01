export default function ScoreBar({ score, showValue = false }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.8
    ? '#e53e3e'
    : score >= 0.5
    ? '#ed8936'
    : score >= 0.3
    ? '#ecc94b'
    : '#68d391'

  return (
    <div className="score-bar-wrap">
      <div className="score-bar">
        <div
          className="score-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      {showValue && <span style={{ fontSize: '.8rem', color: '#4a5568' }}>{score.toFixed(2)}</span>}
    </div>
  )
}
