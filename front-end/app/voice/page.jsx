"use client";

import "./voice.css";
import React, { useRef } from "react";

function Voice() {
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const wsRef = useRef(null);
  const audioBufferRef = useRef([]);

  wsRef.current = new WebSocket(
      `${process.env.NEXT_PUBLIC_API_URL.replace(
        "http",
        "ws"
      )}/ws?token=${token}`
    );
  wsRef.current.onopen = async () => {
      wsRef.current.send(
        JSON.stringify({
          type: "config",
          config: config,
        })
      );
  await startAudioStream();

  wsRef.current.onmessage = async (event) => {
      const response = JSON.parse(event.data);
      if (response.type === "audio") {
        const audioData = base64ToFloat32Array(response.data);
        playAudioData(audioData);
      } else if (response.type === "interrupt") {
        console.log("Received interrupt confirmation from server:", response);
      } else if (response.type === "interrupt_confirmed") {
        console.log("Received interrupt_confirmed from Gemini API:", response);
      } else if (response.type === "stop_audio") {
        console.log("Received stop_audio command from server");
      }
    };

  };



  // Initialize audio context and stream
  const startAudioStream = async () => {
    try {
      // Initialize audio context
      audioContextRef.current = new window.AudioContext({
        sampleRate: 16000, // Required by Gemini
      });
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      console.log("Audio stream started");

      // Create audio input node
      const source = audioContextRef.current.createMediaStreamSource(stream);
      await audioContextRef.current.audioWorklet.addModule("/audio_processor.js");
      const processor = new AudioWorkletNode(
        audio_processor,
        "audio-processor",
        {
          numberOfInputs: 1,
          numberOfOutputs: 1,
          channelCount: 1,
        }
      );

      processor.port.onmessage=(e)=>{
        const inputData = new Float32Array(e.data);

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            const pcmData = float32ToPcm16(inputData);
            const base64Data = btoa(
              String.fromCharCode(...new Uint8Array(pcmData.buffer))
            );
            wsRef.current.send(
              JSON.stringify({
                type: "audio",
                data: base64Data,
              })
            );
          }
      }
      
      source.connect(processor);
      processor.connect(audioContextRef.current.destination);

      audioInputRef.current = { source, processor, stream };
    } catch (err) {
      setError("Failed to access microphone: " + err.message);
    }
  };

  const playAudioData = async (audioData) => {
    
    audioBufferRef.current = [];

    // Add new audio data to queue
    audioBufferRef.current.push(audioData);

    // If nothing is playing, start playback
    
      playNextChunk();
  };

  const playNextChunk = async () => {

    // Get the next chunk from queue
    const chunk = audioBufferRef.current.shift();

    // Create buffer and source
    const buffer = audioContextRef.current.createBuffer(1, chunk.length, 24000);
    buffer.copyToChannel(chunk, 0);

    const source = audioContextRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContextRef.current.destination);

    // Start playing immediately
    source.start(0);

    // When this chunk ends, play the next one
    source.onended = () => {
      if (audioBufferRef.current.length > 0) {
        playNextChunk();
      }
    };
  };
  };

  return (
    <div>
      <div>Voice test</div>

      <button className="record_btn">
        Record
      </button>
    </div>
  );

export default Voice;