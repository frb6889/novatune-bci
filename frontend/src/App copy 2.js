import { useState, useEffect } from "react";

export default function PianoLesson() {
  const [message, setMessage] = useState("等待 MIDI 输入...");
  const [notes, setNotes] = useState([]);
  const [targetNote, setTargetNote] = useState(60); // 初始目标音符

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const { note, expected, result } = data;

      setNotes((prev) => [...prev, note]);

      if (result === true) {
        setMessage(`${result}! 按了 ${note}，下一个该按: ${expected}`);
        setTargetNote(expected); // 更新目标音符
      } else {
        setMessage(`❌ 错误！你按了: ${note}，应该按: ${expected}`);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="p-6 text-center">
      <h1 className="text-xl font-bold">MIDI 练习助手</h1>
      <p>{message}</p>
      <p>当前目标音符: {targetNote}</p>
      <p>弹奏记录: {notes.join(", ")}</p>
    </div>
  );
}
