import { useState, useCallback, useRef, useEffect } from 'react'
import styles from './InlineAdd.module.css'

interface InlineAddProps {
  placeholder: string
  buttonText: string
  onAdd: (value: string) => void
  // For two-field inputs (like boundaries, misconceptions)
  secondPlaceholder?: string
  onAddTwo?: (value1: string, value2: string) => void
}

export function InlineAdd({
  placeholder,
  buttonText,
  onAdd,
  secondPlaceholder,
  onAddTwo,
}: InlineAddProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [value, setValue] = useState('')
  const [secondValue, setSecondValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const isTwoField = !!secondPlaceholder && !!onAddTwo

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isEditing])

  const handleSubmit = useCallback(() => {
    if (isTwoField) {
      if (value.trim() && secondValue.trim() && onAddTwo) {
        onAddTwo(value.trim(), secondValue.trim())
        setValue('')
        setSecondValue('')
        setIsEditing(false)
      }
    } else {
      if (value.trim()) {
        onAdd(value.trim())
        setValue('')
        setIsEditing(false)
      }
    }
  }, [value, secondValue, onAdd, onAddTwo, isTwoField])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      } else if (e.key === 'Escape') {
        setValue('')
        setSecondValue('')
        setIsEditing(false)
      }
    },
    [handleSubmit]
  )

  const handleCancel = useCallback(() => {
    setValue('')
    setSecondValue('')
    setIsEditing(false)
  }, [])

  if (!isEditing) {
    return (
      <button className={styles.addBtn} onClick={() => setIsEditing(true)}>
        {buttonText}
      </button>
    )
  }

  return (
    <div className={styles.inputContainer}>
      <input
        ref={inputRef}
        type="text"
        className={styles.input}
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      {isTwoField && (
        <input
          type="text"
          className={styles.input}
          placeholder={secondPlaceholder}
          value={secondValue}
          onChange={(e) => setSecondValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
      )}
      <div className={styles.actions}>
        <button className={styles.submitBtn} onClick={handleSubmit}>
          Add
        </button>
        <button className={styles.cancelBtn} onClick={handleCancel}>
          Cancel
        </button>
      </div>
    </div>
  )
}
