class AudioProcessor extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input = inputs[0];

    if (!input || !input[0]) {
      return true;
    }

    const inputData = input[0];

    // Ignore completely silent buffers
    let hasAudio = false;

    for (let i = 0; i < inputData.length; i++) {
      if (inputData[i] !== 0) {
        hasAudio = true;
        break;
      }
    }

    if (!hasAudio) {
      return true;
    }

    // Send Float32Array to main thread.
    // Transfer the underlying ArrayBuffer to avoid copying.
    const data = new Float32Array(inputData);

    this.port.postMessage(data.buffer, [data.buffer]);

    return true;
  }
}

registerProcessor("audio_processor", AudioProcessor);