import { useState } from 'react';
import { generateQuiz, generateFlashcards, summarizeDocuments } from '../services/api';

export default function StudyTools({ model }) {
  const [loading, setLoading] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [flashcardData, setFlashcardData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [flippedCards, setFlippedCards] = useState({});
  const [alert, setAlert] = useState(null);

  const showAlert = (type, message) => {
    setAlert({ type, message });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleGenerateQuiz = async () => {
    setLoading('quiz');
    try {
      const data = await generateQuiz(model, 5);
      setQuizData(data);
      setSelectedAnswers({});
    } catch (err) {
      showAlert('error', err.response?.data?.detail || 'Failed to generate quiz');
    } finally {
      setLoading(null);
    }
  };

  const handleGenerateFlashcards = async () => {
    setLoading('flashcards');
    try {
      const data = await generateFlashcards(model, 8);
      setFlashcardData(data);
      setFlippedCards({});
    } catch (err) {
      showAlert('error', err.response?.data?.detail || 'Failed to generate flashcards');
    } finally {
      setLoading(null);
    }
  };

  const handleSummarize = async () => {
    setLoading('summary');
    try {
      const data = await summarizeDocuments(model);
      setSummaryData(data);
    } catch (err) {
      showAlert('error', err.response?.data?.detail || 'Failed to generate summary');
    } finally {
      setLoading(null);
    }
  };

  const handleSelectAnswer = (qIdx, optIdx, correctIdx) => {
    if (selectedAnswers[qIdx] !== undefined) return;
    setSelectedAnswers((prev) => ({ ...prev, [qIdx]: optIdx }));
  };

  const toggleFlashcard = (idx) => {
    setFlippedCards((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="study-container">
      <h2>🎓 Study Tools</h2>
      <p>Generate quizzes, flashcards, and summaries from your uploaded documents using AI</p>

      {alert && <div className={`alert ${alert.type}`}>{alert.message}</div>}

      {/* Tool Cards */}
      <div className="study-tools-grid">
        <div className="study-tool-card">
          <div className="tool-icon">📝</div>
          <h3>Quiz Generator</h3>
          <p>Generate multiple-choice questions to test your knowledge</p>
          <button
            className="generate-btn"
            onClick={handleGenerateQuiz}
            disabled={loading === 'quiz'}
          >
            {loading === 'quiz' ? '⏳ Generating...' : '✨ Generate Quiz'}
          </button>
        </div>

        <div className="study-tool-card">
          <div className="tool-icon">🃏</div>
          <h3>Flashcards</h3>
          <p>Create study flashcards for quick revision sessions</p>
          <button
            className="generate-btn"
            onClick={handleGenerateFlashcards}
            disabled={loading === 'flashcards'}
          >
            {loading === 'flashcards' ? '⏳ Generating...' : '✨ Generate Cards'}
          </button>
        </div>

        <div className="study-tool-card">
          <div className="tool-icon">📋</div>
          <h3>Smart Summary</h3>
          <p>Get a concise summary with key points from your documents</p>
          <button
            className="generate-btn"
            onClick={handleSummarize}
            disabled={loading === 'summary'}
          >
            {loading === 'summary' ? '⏳ Analyzing...' : '✨ Summarize'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>AI is processing your documents...</p>
        </div>
      )}

      {/* Quiz Results */}
      {quizData && quizData.questions?.length > 0 && (
        <div className="quiz-section">
          <h3 style={{ marginBottom: 16 }}>📝 Quiz: {quizData.topic}</h3>
          {quizData.questions.map((q, qIdx) => (
            <div key={qIdx} className="quiz-question-card">
              <div className="quiz-q-number">Question {qIdx + 1}</div>
              <h4>{q.question}</h4>
              <div className="quiz-options">
                {q.options.map((opt, optIdx) => {
                  let optClass = 'quiz-option';
                  if (selectedAnswers[qIdx] !== undefined) {
                    optClass += ' disabled';
                    if (optIdx === q.correct) optClass += ' correct';
                    else if (optIdx === selectedAnswers[qIdx]) optClass += ' wrong';
                  }
                  return (
                    <button
                      key={optIdx}
                      className={optClass}
                      onClick={() => handleSelectAnswer(qIdx, optIdx, q.correct)}
                      disabled={selectedAnswers[qIdx] !== undefined}
                    >
                      {String.fromCharCode(65 + optIdx)}. {opt}
                    </button>
                  );
                })}
              </div>
              {selectedAnswers[qIdx] !== undefined && q.explanation && (
                <div className="quiz-explanation">
                  💡 {q.explanation}
                </div>
              )}
            </div>
          ))}
          <div style={{ textAlign: 'center', marginTop: 16, color: 'var(--text-muted)' }}>
            Score: {Object.entries(selectedAnswers).filter(([qIdx, ans]) =>
              quizData.questions[qIdx]?.correct === ans
            ).length} / {quizData.questions.length}
          </div>
        </div>
      )}

      {/* Flashcards */}
      {flashcardData && flashcardData.cards?.length > 0 && (
        <div className="flashcard-section">
          <h3 style={{ marginBottom: 16 }}>🃏 Flashcards: {flashcardData.topic}</h3>
          <div className="flashcards-grid">
            {flashcardData.cards.map((card, idx) => (
              <div
                key={idx}
                className={`flashcard ${flippedCards[idx] ? 'flipped' : ''}`}
                onClick={() => toggleFlashcard(idx)}
              >
                <div className="flashcard-label">
                  {flippedCards[idx] ? '✅ Answer' : '❓ Question'}
                </div>
                <div className="flashcard-text">
                  {flippedCards[idx] ? card.back : card.front}
                </div>
                <span className="flip-hint">Click to flip</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {summaryData && (
        <div className="summary-result">
          <div className="summary-card">
            <h3>📋 Document Summary</h3>
            <p className="summary-text">{summaryData.summary}</p>
          </div>

          {summaryData.key_points?.length > 0 && (
            <div className="summary-card">
              <h3>🔑 Key Points</h3>
              <ul className="key-points">
                {summaryData.key_points.map((point, idx) => (
                  <li key={idx}>
                    <span className="key-point-bullet">▸</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Source content: ~{summaryData.word_count} words analyzed
          </div>
        </div>
      )}
    </div>
  );
}
