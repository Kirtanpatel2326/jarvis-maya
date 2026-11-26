export class WakeWordEngine {
  private recognition: any = null;
  private isActive: boolean = false;
  private isSpeaking: boolean = false;
  private onWakeCallback: (() => void) | null = null;
  private onCommandCallback: ((text: string) => void) | null = null;

  constructor(onWake: () => void, onCommand: (text: string) => void) {
    this.onWakeCallback = onWake;
    this.onCommandCallback = onCommand;
    this.init();
  }

  public setSpeaking(speaking: boolean) {
    this.isSpeaking = speaking;
  }

  private init() {
    if (typeof window === 'undefined') return;

    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) return;

    this.recognition = new SpeechRec();
    this.recognition.continuous = true;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';

    this.recognition.onresult = (event: any) => {
      if (this.isSpeaking) return; // Mute shielding while TTS speaks

      const lastIndex = event.results.length - 1;
      const transcript = event.results[lastIndex][0].transcript.trim();
      if (!transcript) return;

      const lower = transcript.toLowerCase();

      if (lower.includes('hey jarvis') || lower.includes('jarvis')) {
        if (this.onWakeCallback) this.onWakeCallback();

        const cleanCmd = lower.replace(/hey jarvis|jarvis/g, '').trim();
        if (cleanCmd && this.onCommandCallback) {
          this.onCommandCallback(cleanCmd);
        }
      } else if (this.isActive && this.onCommandCallback) {
        this.onCommandCallback(transcript);
      }
    };

    this.recognition.onerror = (err: any) => {
      if (this.isActive && !this.isSpeaking) {
        setTimeout(() => this.start(), 1000);
      }
    };

    this.recognition.onend = () => {
      if (this.isActive && !this.isSpeaking) {
        setTimeout(() => this.start(), 400);
      }
    };
  }

  public start() {
    this.isActive = true;
    try {
      this.recognition?.start();
    } catch {
      // Already running
    }
  }

  public stop() {
    this.isActive = false;
    try {
      this.recognition?.stop();
    } catch {
      // Already stopped
    }
  }
}
