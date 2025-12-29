import { useResearchData } from '../../store/useStore'
import styles from './KeyIdeasTab.module.css'

export function KeyIdeasTab() {
  const researchData = useResearchData()

  if (!researchData || researchData.keyIdeas.length === 0) {
    return (
      <div className={styles.empty}>
        No key ideas captured yet. Key ideas are concepts that help answer multiple questions.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Research</div>
        <h1 className={styles.title}>{researchData.topic}</h1>
        <p className={styles.description}>
          Key ideas are concepts that transcend individual questions and help answer multiple parts of your research.
        </p>
      </div>

      <div className={styles.ideas}>
        {researchData.keyIdeas.map((idea) => (
          <div key={idea.id} className={styles.idea}>
            <div className={styles.ideaIcon}>💡</div>
            <div className={styles.ideaContent}>
              <h3 className={styles.ideaTitle}>{idea.title}</h3>
              <p className={styles.ideaDescription}>{idea.description}</p>
              <div className={styles.relevance}>
                <span className={styles.relevanceLabel}>Relevance:</span>
                <span className={styles.relevanceText}>{idea.relevance}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button className={styles.addBtn}>+ Add key idea</button>
    </div>
  )
}
