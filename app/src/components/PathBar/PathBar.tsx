import { usePath } from '../../store/useStore'
import styles from './PathBar.module.css'

export function PathBar() {
  const path = usePath()

  return (
    <div className={styles.pathBar}>
      <span className={styles.pathLabel}>Path</span>
      <div className={styles.pathTrail}>
        {path.nodes.map((node, i) => (
          <span key={node.id} className={styles.pathSegment}>
            <div
              className={`${styles.pathNode} ${i === path.nodes.length - 1 ? styles.current : ''}`}
            >
              <span className={`${styles.nodeDot} ${styles[node.status]}`}></span>
              {node.name}
            </div>
            {i < path.nodes.length - 1 && <span className={styles.pathArrow}>→</span>}
          </span>
        ))}
      </div>
      <div className={styles.pathDivider}></div>
      <span className={styles.neighborsLabel}>Explore</span>
      <div className={styles.neighborChips}>
        {path.neighbors.map((neighbor) => (
          <div key={neighbor} className={styles.neighborChip}>
            {neighbor}
          </div>
        ))}
      </div>
    </div>
  )
}
