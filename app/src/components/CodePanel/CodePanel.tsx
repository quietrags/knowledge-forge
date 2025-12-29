import { Highlight, themes } from 'prism-react-renderer'
import { useCurrentCode } from '../../store/useStore'
import styles from './CodePanel.module.css'

export function CodePanel() {
  const code = useCurrentCode()

  if (!code) {
    return (
      <div className={styles.panel}>
        <div className={styles.header}>
          <span className={styles.title}>Code</span>
        </div>
        <div className={styles.body}>
          <div className={styles.empty}>Select a question to view related code</div>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>Code</span>
      </div>
      <div className={styles.body}>
        <div className={styles.fileHeader}>
          <span className={styles.fileIcon}>📄</span>
          <span className={styles.fileName}>{code.file}</span>
        </div>
        <Highlight
          theme={themes.nightOwl}
          code={code.content}
          language={code.language || 'python'}
        >
          {({ className, style, tokens, getLineProps, getTokenProps }) => (
            <pre className={`${className} ${styles.codeBlock}`} style={style}>
              {tokens.map((line, i) => (
                <div key={i} {...getLineProps({ line })}>
                  {line.map((token, key) => (
                    <span key={key} {...getTokenProps({ token })} />
                  ))}
                </div>
              ))}
            </pre>
          )}
        </Highlight>
        {code.library && (
          <div className={styles.libraryRef}>
            <div className={styles.libraryLabel}>Library</div>
            <a href={code.library.url} target="_blank" rel="noopener noreferrer">
              {code.library.name}
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
