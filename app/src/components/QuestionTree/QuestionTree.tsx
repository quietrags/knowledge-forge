import { useState, useCallback } from 'react'
import { useResearchData, useSelectedQuestionId, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
import type { CategoryQuestion, Question } from '../../types'
import styles from './QuestionTree.module.css'

// Status icons - updated to match new QuestionStatus
const STATUS_ICONS = {
  answered: '✓',
  investigating: '◐',
  open: '○',
}

// Source credibility badge
function SourceBadge({ credibility }: { credibility: string }) {
  return (
    <span className={`${styles.credBadge} ${styles[credibility]}`}>
      {credibility}
    </span>
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
    onSelect()
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
        <div className={styles.questionBody} onClick={(e) => e.stopPropagation()}>
          {question.answer ? (
            <div className={styles.answer}>
              <div className={styles.answerLabel}>Answer</div>
              <div className={styles.answerText}>{question.answer}</div>
            </div>
          ) : (
            <div className={styles.researching}>
              {question.status === 'investigating' ? 'Investigating...' : 'Not yet started'}
            </div>
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
        </div>
      )}
    </div>
  )
}

// Category section - now uses CategoryQuestion and fetches questions by ID
function CategorySection({
  category,
  questions,
  expandedIds,
  selectedId,
  onToggle,
  onSelect,
  onAddQuestion,
}: {
  category: CategoryQuestion
  questions: Question[]
  expandedIds: Set<string>
  selectedId: string | null
  onToggle: (id: string) => void
  onSelect: (id: string) => void
  onAddQuestion: (categoryId: string, text: string) => void
}) {
  return (
    <div className={styles.category}>
      <div className={styles.categoryHeader}>
        <div className={styles.categoryTitle}>
          <span className={styles.categoryIcon}>📂</span>
          {category.category}
        </div>
        {category.insight && (
          <div className={styles.categoryInsight}>
            <span className={styles.insightLabel}>Insight:</span> {category.insight}
          </div>
        )}
      </div>
      <div className={styles.questionList}>
        {questions.map((question) => (
          <QuestionItem
            key={question.id}
            question={question}
            isExpanded={expandedIds.has(question.id)}
            isSelected={selectedId === question.id}
            onToggle={() => onToggle(question.id)}
            onSelect={() => onSelect(question.id)}
          />
        ))}
        <InlineAdd
          placeholder="Enter question..."
          buttonText="+ Add question"
          onAdd={(text) => onAddQuestion(category.id, text)}
        />
      </div>
    </div>
  )
}

// Main QuestionTree component
export function QuestionTree() {
  const researchData = useResearchData()
  const selectedQuestionId = useSelectedQuestionId()
  const { selectQuestion, addQuestion, addCategory } = useForgeActions()
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
      setExpandedIds((prev) => {
        if (prev.has(id)) return prev
        return new Set([...prev, id])
      })
    },
    [selectQuestion]
  )

  const handleAddQuestion = useCallback(
    (categoryId: string, text: string) => {
      addQuestion(categoryId, text)
    },
    [addQuestion]
  )

  const handleAddCategory = useCallback(
    (name: string) => {
      addCategory(name)
    },
    [addCategory]
  )

  if (!researchData) {
    return (
      <div className={styles.empty}>
        No research data available. Start a research session to see questions.
      </div>
    )
  }

  // Helper to get questions for a category
  const getQuestionsForCategory = (categoryId: string): Question[] => {
    return researchData.questions.filter((q) => q.categoryId === categoryId)
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
            questions={getQuestionsForCategory(category.id)}
            expandedIds={expandedIds}
            selectedId={selectedQuestionId}
            onToggle={handleToggle}
            onSelect={handleSelect}
            onAddQuestion={handleAddQuestion}
          />
        ))}
        <InlineAdd
          placeholder="Enter category name..."
          buttonText="+ Add question category"
          onAdd={handleAddCategory}
        />
      </div>
    </div>
  )
}
