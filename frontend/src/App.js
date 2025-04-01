import { useState, useEffect, useRef } from "react";
import './App.css';
import { KEY_CONFIG } from './key_config';
import { ProgressPopup } from "./components/progress_popup";

// 定义各段落的简谱信息
const songSections = [
  "5 5 6 2 - 1 1 _6 2 -",
  "5 5 6 ·1 6 5 1 1 _6 2 -",
  "5 2 1 _7 _6 _5 5 2",
  "3 2 1 1 _6 2 3 2 1 2 1 _7 _6 _5 ",
  "5 2 1 _7 _6 _5 5 2,",
  "3 2 1 1 _6 2 3 2 1 ·2 ·1 7 6 5 - 5 0"
];

export default function PianoLesson() {
  const [message, setMessage] = useState("等待 MIDI 输入...");
  const [notes, setNotes] = useState([]);
  const [targetNote, setTargetNote] = useState(60);
  const [nextTargetNote, setNextTargetNote] = useState(null);
  const [activeKeys, setActiveKeys] = useState([]);
  const [showPopup, setShowPopup] = useState(false);
  const [popupKey, setPopupKey] = useState(0);
  const [progress, setProgress] = useState(0);
  const [popupNote, setPopupNote] = useState("C4");
  const [section, setSection] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedNotes, setRecordedNotes] = useState([]);

  const timerRef = useRef(null);
  const intervalRef = useRef(null);
  const wsRef = useRef(null);

  const clearTimers = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);
  };

  const startNextNoteCountdown = (newNote) => {
    clearTimers();
    setProgress(0);


    const totalDuration = 2500;
    const intervalTime = 16; // 约60FPS

    intervalRef.current = setInterval(() => {
      setProgress(prev => Math.min(prev + (100 / (totalDuration / intervalTime)), 100));
    }, intervalTime);

    timerRef.current = setTimeout(() => {
      setTargetNote(newNote);
      const noteConfig = KEY_CONFIG.find(k => k.note === newNote);
      setPopupNote(noteConfig?.name || "");
      setPopupKey(prev => prev + 1);
      setProgress(0);
      clearTimers();
    }, totalDuration);
  };

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const { type, note, expected, result, section: newSection } = data;

      if (type === 'section_update') {
        setSection(newSection);
        setTargetNote(expected);
        // 根据新的 targetNote 更新 popupNote
        const noteConfig = KEY_CONFIG.find(k => k.note === expected);
        setPopupNote(noteConfig?.name || "");
        setMessage(`切换到第 ${newSection} 段`);
        return;
      }

      setNotes(prev => [...prev, note]);
      if (isRecording) {
        setRecordedNotes(prev => [...prev, note]);
      }

      if (!isMuted && type === 'note_on') {
        setActiveKeys(prev => [...prev, note]);

        if (result === true) {
          setMessage("✅ 正确!");
          setNextTargetNote(note);
          startNextNoteCountdown(expected);
        } else {
          setMessage("❌ 错误");
        }
      } else if (type === 'note_off') {
        setActiveKeys(prev => prev.filter(n => n !== note));
      }
    };

    return () => {
      ws.close();
      clearTimers();
    };
  }, [isMuted, isRecording]);

  useEffect(() => {
    setShowPopup(true);
  }, [popupKey]);

  const expectedNoteName = KEY_CONFIG.find(key => key.note === targetNote)?.name || "未知音符";

  const toggleMute = () => {
    setIsMuted(prev => !prev);
  };

  const toggleRecording = () => {
    if (isRecording) {
      const blob = new Blob([JSON.stringify(recordedNotes)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "recorded_notes.json";
      a.click();
      URL.revokeObjectURL(url);
    }
    setIsRecording(prev => !prev);
    setRecordedNotes([]);
  };

  return (
    <div className="app">
      {showPopup && (
        <ProgressPopup
          noteName={popupNote}
          progress={progress}
          onClose={() => {
            setShowPopup(false);
            clearTimers();
          }}
        />
      )}
      <div >
        <p>当前段落: {section}  <br /> 简谱：</p>

        <p className="puzi">{songSections[section - 1]}</p>

      </div>

      <div className="piano-container">

        <div className="piano">
          {KEY_CONFIG.map((keyConfig) => {
            const isActive = activeKeys.includes(keyConfig.note);
            const showIndicator = keyConfig.name === popupNote;
            return (
              // 修改钢琴键的渲染部分
              <div
                key={keyConfig.note}
                className={`key white ${showIndicator ? "has-indicator" : ""} ${isActive ? "active" : ""} `}
              >
                <div className="key-body">
                  <div className="key-label">{keyConfig.name}</div>

                </div>
                {keyConfig.blackKey && (
                  <img
                    src="/black_key.png"
                    className="black-key"
                    style={{
                      [keyConfig.blackKey.position]: keyConfig.blackKey.offset,
                      height: keyConfig.blackKey.height
                    }}
                    alt="黑键"
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      <p>{message}</p>
      <p>弹奏记录: {notes.join(", ")}</p>


      <button onClick={toggleMute}>{isMuted ? "取消静音" : "静音"}</button>
      <button onClick={toggleRecording}>{isRecording ? "停止录音" : "开始录音"}</button>
    </div>
  );
}
