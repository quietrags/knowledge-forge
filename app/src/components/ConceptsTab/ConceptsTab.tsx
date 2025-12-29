import { useBuildData } from '../../store/useStore'
import styles from './ConceptsTab.module.css'

export function ConceptsTab() {
  const buildData = useBuildData()

  if (!buildData || buildData.concepts.length === 0) {
    return (
      <div className={styles.empty}>
        No concepts defined yet. Concepts are the key terms and definitions you're learning.
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.label}>Building</div>
        <h1 className={styles.title}>{buildData.narrative.title}</h1>
        <p className={styles.description}>
          Key concepts and their definitions—the vocabulary of your learning domain.
        </p>
      </div>

      <div className={styles.concepts}>
        {buildData.concepts.map((concept) => (
          <div key={concept.id} className={styles.concept}>
            <div className={styles.term}>{concept.term}</div>
            <div className={styles.definition}>{concept.definition}</div>
          </div>
        ))}
      </div>

      <button className={styles.addBtn}>+ Add concept</button>
    </div>
  )
}
