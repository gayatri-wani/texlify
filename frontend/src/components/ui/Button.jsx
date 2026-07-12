import './Button.css'

const Button = ({ children, loading, variant = 'primary', size = 'md', fullWidth = true, ...props }) => {
  return (
    <button
      className={[
        'btn',
        `btn--${variant}`,
        `btn--${size}`,
        fullWidth ? 'btn--full' : '',
        loading ? 'btn--loading' : '',
      ].filter(Boolean).join(' ')}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <span className="btn-spinner" />}
      <span className={`btn-label ${loading ? 'btn-label--hidden' : ''}`}>
        {children}
      </span>
    </button>
  )
}

export default Button