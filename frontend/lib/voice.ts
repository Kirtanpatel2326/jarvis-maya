// frontend/lib/voice.ts

export class VoicePipeline {
  private recognition: any = null;
  private isListening: boolean = false;

  constructor() {
    if (typeof window !== 'undefined') {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
      }
    }
  }

  public listen(onResult: (text: string) => void, onEnd?: () => void) {
    if (!this.recognition || this.isListening) return;

    this.isListening = true;
    try {
      this.recognition.start();
    } catch {
      this.isListening = false;
      if (onEnd) onEnd();
      return;
    }

    this.recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };

    this.recognition.onerror = (err: any) => {
      console.warn('Speech recognition error:', err);
      this.isListening = false;
      if (onEnd) onEnd();
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (onEnd) onEnd();
    };
  }

  public speak(text: string) {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 0.95;

      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (v) => v.name.includes('Daniel') || v.name.includes('Google UK English Male') || v.lang === 'en-GB'
      );
      if (preferredVoice) utterance.voice = preferredVoice;

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis error:', e);
    }
  }
}

export const voice = new VoicePipeline();
