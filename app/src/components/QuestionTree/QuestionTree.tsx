import { useState, useCallback } from 'react'
import { useResearchData, useSelectedQuestionId, useForgeActions } from '../../store/useStore'
import { InlineAdd } from '../InlineAdd/InlineAdd'
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
  onAddSubQuestion,
}: {
  question: Question
  isExpanded: boolean
  isSelected: boolean
  onToggle: () => void
  onSelect: () => void
  onAddSubQuestion: (text: string) => void
}) {
  const handleHeaderClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    onToggle()
    onSelect() // Also select when clicking header
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

          <div className={styles.subQuestions}>
            <div className={styles.subQuestionsLabel}>Sub-questions</div>
            {question.subQuestions.map((sq) => (
              <SubQuestionItem key={sq.id} subQuestion={sq} />
            ))}
            <InlineAdd
              placeholder="Enter sub-question..."
              buttonText="+ Add sub-question"
              onAdd={onAddSubQuestion}
            />
          </div>
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
  onAddQuestion,
  onAddSubQuestion,
}: {
  category: Category
  expandedIds: Set<string>
  selectedId: string | null
  onToggle: (id: string) => void
  onSelect: (id: string) => void
  onAddQuestion: (categoryId: string, text: string) => void
  onAddSubQuestion: (questionId: string, text: string) => void
}) {
  return (
    <div className={styles.category}>
      <div className={styles.categoryHeader}>
        <div className={styles.categoryTitle}>
          <span className={styles.categoryIcon}>📂</span>
          {category.name}
        </div>
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
            onAddSubQuestion={(text) => onAddSubQuestion(question.id, text)}
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
  const { selectQuestion, addQuestion, addSubQuestion, addCategory } = useForgeActions()
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

  const handleAddQuestion = useCallback(
    (categoryId: string, text: string) => {
      addQuestion(categoryId, text)
    },
    [addQuestion]
  )

  const handleAddSubQuestion = useCallback(
    (questionId: string, text: string) => {
      addSubQuestion(questionId, text)
    },
    [addSubQuestion]
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
            onAddQuestion={handleAddQuestion}
            onAddSubQuestion={handleAddSubQuestion}
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
