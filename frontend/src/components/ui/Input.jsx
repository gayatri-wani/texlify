import './Input.css'

const Input = ({ label, error, icon: Icon, hint, ...props }) => {
  return (
    <div className="input-wrapper">

      {label && (
        <label className="input-label">{label}</label>
      )}

      <div className={`input-container ${error ? 'input-container--error' : ''}`}>
        {Icon && (
          <span className="input-icon">
            <Icon size={16} />
          </span>
        )}
        <input
          className={`input-field ${Icon ? 'input-field--with-icon' : ''}`}
          {...props}
        />
      </div>

      {error && <span className="input-error">{error}</span>}
      {hint && !error && <span className="input-hint">{hint}</span>}

    </div>
  )
}

export default Input