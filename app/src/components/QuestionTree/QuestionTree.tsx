import { useState, useCallback } from 'react'
import { useResearchData, useSelectedQuestionId, useForgeActions } from '../../store/useStore'
import type { Category, Question } from '../../types'
import styles from './QuestionTree.module.css'

// Status icons
const STATUS_ICONS = {
  answered: '✓',
  researching: '◐',
  pending: '○',
}

// Source credibility badge
function SourceBadge({ credibility }: { credibility: string }) {
  return (
    <span className={`${styles.credBadge} ${styles[credibility]}`}>
      {credibility}
    </span>
  )
}

// Sub-question item
function SubQuestionItem({ subQuestion }: { subQuestion: { id: string; question: string; status: string } }) {
  return (
    <div className={`${styles.subQuestion} ${styles[subQuestion.status]}`}>
      <span className={styles.subQuestionArrow}>↳</span>
      <span>{subQuestion.question}</span>
    </div>
  )
}

// Question item
function QuestionItem({
  question,
  isExpanded,
  isSelected,
  onToggle,
  onSelect,
}: {
  question: Question
  isExpanded: boolean
  isSelected: boolean
  onToggle: () => void
  onSelect: () => void
}) {
  const handleHeaderClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onToggle()
  }

  const handleCardClick = () => {
    onSelect()
  }

  return (
    <div
      className={`${styles.question} ${styles[question.status]} ${isExpanded ? styles.expanded : ''} ${isSelected ? styles.selected : ''}`}
      onClick={handleCardClick}
    >
      <div className={styles.questionHeader} onClick={handleHeaderClick}>
        <div className={`${styles.statusIcon} ${styles[question.status]}`}>
          {STATUS_ICONS[question.status]}
        </div>
        <div className={styles.questionContent}>
          <div className={styles.questionText}>{question.question}</div>
        </div>
        <div className={styles.toggleIcon}>{isExpanded ? '▲' : '▼'}</div>
      </div>

      {isExpanded && (
        <div className={styles.questionBody}>
          {question.answer ? (
            <div className={styles.answer}>
              <div className={styles.answerLabel}>Answer</div>
              <div className={styles.answerText}>{question.answer}</div>
            </div>
          ) : (
            <div className={styles.researching}>Researching...</div>
          )}

          {question.sources.length > 0 && (
            <div className={styles.sources}>
              <div className={styles.sourcesLabel}>Sources</div>
              <div className={styles.sourcesList}>
                {question.sources.map((source, i) => (
                  <span key={i} className={styles.source}>
                    {source.url ? (
                      <a href={source.url} target="_blank" rel="noopener noreferrer">
                        {source.title}
                      </a>
                    ) : (
                      <span>{source.title}</span>
                    )}
                    <SourceBadge credibility={source.credibility} />
                  </span>
                ))}
              </div>
            </div>
          )}

          {question.subQuestions && question.subQuestions.length > 0 && (
            <div className={styles.subQuestions}>
              <div className={styles.subQuestionsLabel}>Sub-questions</div>
              {question.subQuestions.map((sq) => (
                <SubQuestionItem key={sq.id} subQuestion={sq} />
              ))}
              <button className={styles.addBtn}>+ Add</button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Category section
function CategorySection({
  category,
  expandedIds,
  selectedId,
  onToggle,
  onSelect,
}: {
  category: Category
  expandedIds: Set<string>
  selectedId: string | null
  onToggle: (id: string) => void
  onSelect: (id: string) => void
}) {
  return (
    <div className={styles.category}>
      <div className={styles.categoryHeader}>
        <div className={styles.categoryTitle}>
          <span className={styles.categoryIcon}>📂</span>
          {category.name}
        </div>
        <button className={styles.categoryAddBtn}>+ Add question</button>
      </div>
      <div className={styles.questionList}>
        {category.questions.map((question) => (
          <QuestionItem
            key={question.id}
            question={question}
            isExpanded={expandedIds.has(question.id)}
            isSelected={selectedId === question.id}
            onToggle={() => onToggle(question.id)}
            onSelect={() => onSelect(question.id)}
          />
        ))}
        <button className={styles.addBtn}>+ Add sub-question</button>
      </div>
    </div>
  )
}

// Main QuestionTree component
export function QuestionTree() {
  const researchData = useResearchData()
  const selectedQuestionId = useSelectedQuestionId()
  const { selectQuestion } = useForgeActions()
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const handleToggle = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const handleSelect = useCallback(
    (id: string) => {
      selectQuestion(id)
      // Also expand if not already
      setExpandedIds((prev) => {
        if (prev.has(id)) return prev
        return new Set([...prev, id])
      })
    },
    [selectQuestion]
  )

  if (!researchData) {
    return (
      <div className={styles.empty}>
        No research data available. Start a research session to see questions.
      </div>
    )
  }

  return (
    <div className={styles.tree}>
      <div className={styles.header}>
        <div className={styles.headerLabel}>Research</div>
        <h1 className={styles.headerTitle}>{researchData.topic}</h1>
        <div className={styles.headerMeta}>{researchData.meta}</div>
      </div>

      <div className={styles.categories}>
        {researchData.categories.map((category) => (
          <CategorySection
            key={category.id}
            category={category}
            expandedIds={expandedIds}
            selectedId={selectedQuestionId}
            onToggle={handleToggle}
            onSelect={handleSelect}
          />
        ))}
        <button className={styles.addCategoryBtn}>+ Add question category</button>
      </div>
    </div>
  )
}
