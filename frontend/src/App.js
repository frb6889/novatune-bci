import { useState, useEffect, useRef } from "react";
import './App.css';
import { KEY_CONFIG } from './key_config';
import { ProgressPopup } from "./components/progress_popup";

export default function PianoLesson() {
  const [message, setMessage] = useState("等待 MIDI 输入...");
  const [notes, setNotes] = useState([]);
  const [targetNote, setTargetNote] = useState(60);
  const [nextTargetNote, setNextTargetNote] = useState(null);
  const [activeKeys, setActiveKeys] = useState([]); // 记录当前按下的键

  const [showPopup, setShowPopup] = useState(false);
  const [popupKey, setPopupKey] = useState(0); // 用于强制刷新弹窗
  const [progress, setProgress] = useState(0);
  const [popupNote, setPopupNote] = useState("C4"); // 与指示器同步的目标音符名称

  const timerRef = useRef(null);
  const intervalRef = useRef(null);

  // 清除计时器
  const clearTimers = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);
  };

  // 启动下一个键的倒计时（仅进度条在识别后启动）
  const startNextNoteCountdown = (newNote) => {
    clearTimers();
    setProgress(0);

    // 进度条动画
    let currentProgress = 0;
    intervalRef.current = setInterval(() => {
      currentProgress += 1;
      setProgress(prev => Math.min(prev + (100 / 60), 100));
    }, 30);

    // 3秒后切换目标键
    timerRef.current = setTimeout(() => {
      setTargetNote(newNote);
      // 切换弹窗图标，同时更新 popupNote
      const noteConfig = KEY_CONFIG.find(k => k.note === newNote);
      setPopupNote(noteConfig?.name || "");

      setPopupKey(prev => prev + 1);
      setProgress(0);
      clearTimers();
    }, 3000);
  };

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const { type, note, expected, result } = data;

      setNotes(prev => [...prev, note]);

      if (type === 'note_on') {
        // 更新按下的键（允许多键同时按下）
        setActiveKeys(prev => [...prev, note]);

        if (result === true) {
          setMessage(`✅ 正确!`);
          setNextTargetNote(note);
          startNextNoteCountdown(expected);
        } else {
          setMessage(`❌ 错误`);
        }
      } else if (type === 'note_off') {
        // 移除按键
        setActiveKeys(prev => prev.filter(n => n !== note));
      }
    };

    return () => {
      ws.close();
      clearTimers();
    };
  }, []);

  // 当 popupKey 改变时，显示弹窗
  useEffect(() => {
    setShowPopup(true);
  }, [popupKey]);

  const expectedNoteName = KEY_CONFIG.find(key => key.note === targetNote)?.name || "未知音符";

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
      
      <div className="piano-container">
        <div className="piano">
          {KEY_CONFIG.map((keyConfig) => {
            // 用 activeKeys 来显示真实的按下效果
            const isActive = activeKeys.includes(keyConfig.note);
            // 用 popupNote 来决定三角指示器的显示（与目标音符同步）
            const showIndicator = keyConfig.name === popupNote;
            return (
              <div 
                key={keyConfig.note} 
                className={`key white ${isActive ? "active" : ""}`}
              >
                <div className="key-body">
                  <div className="key-label">{keyConfig.name}</div>
                  {/* 当此键对应当前目标音符时显示三角形指示器 */}
                  {showIndicator && <div className="triangle-indicator"></div>}
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
    </div>
  );
}
