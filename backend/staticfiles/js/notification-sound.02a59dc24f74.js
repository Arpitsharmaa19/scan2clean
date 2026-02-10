// Notification Sound Manager
class NotificationSoundManager {
    constructor() {
        // Create audio context
        this.audioContext = null;
        this.sounds = {};
        this.enabled = localStorage.getItem('notificationSoundsEnabled') !== 'false';
        this.volume = parseFloat(localStorage.getItem('notificationVolume') || '0.7');

        // Initialize audio context on user interaction
        this.initAudioContext();
    }

    initAudioContext() {
        // Initialize on first user interaction
        const initOnInteraction = () => {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                this.generateNotificationSounds();
            }
            document.removeEventListener('click', initOnInteraction);
            document.removeEventListener('touchstart', initOnInteraction);
        };

        document.addEventListener('click', initOnInteraction);
        document.addEventListener('touchstart', initOnInteraction);
    }

    // Generate notification sounds using Web Audio API
    generateNotificationSounds() {
        if (!this.audioContext) return;

        // Success/OTP Sound - Pleasant ascending tones
        this.sounds.success = this.createToneSequence([
            { freq: 523.25, duration: 0.1 },  // C5
            { freq: 659.25, duration: 0.1 },  // E5
            { freq: 783.99, duration: 0.15 }  // G5
        ]);

        // Assignment Sound - Attention-grabbing
        this.sounds.assignment = this.createToneSequence([
            { freq: 659.25, duration: 0.12 },  // E5
            { freq: 783.99, duration: 0.12 },  // G5
            { freq: 659.25, duration: 0.12 },  // E5
            { freq: 783.99, duration: 0.18 }   // G5
        ]);

        // Alert Sound - Urgent
        this.sounds.alert = this.createToneSequence([
            { freq: 880.00, duration: 0.1 },   // A5
            { freq: 0, duration: 0.05 },       // Pause
            { freq: 880.00, duration: 0.1 },   // A5
            { freq: 0, duration: 0.05 },       // Pause
            { freq: 880.00, duration: 0.15 }   // A5
        ]);

        // Message Sound - Gentle notification
        this.sounds.message = this.createToneSequence([
            { freq: 587.33, duration: 0.1 },   // D5
            { freq: 659.25, duration: 0.15 }   // E5
        ]);

        // Error Sound - Descending tones
        this.sounds.error = this.createToneSequence([
            { freq: 493.88, duration: 0.15 },  // B4
            { freq: 392.00, duration: 0.2 }    // G4
        ]);
    }

    createToneSequence(notes) {
        return () => {
            if (!this.enabled || !this.audioContext) return;

            let time = this.audioContext.currentTime;

            notes.forEach(note => {
                if (note.freq > 0) {
                    const oscillator = this.audioContext.createOscillator();
                    const gainNode = this.audioContext.createGain();

                    oscillator.connect(gainNode);
                    gainNode.connect(this.audioContext.destination);

                    oscillator.frequency.value = note.freq;
                    oscillator.type = 'sine';

                    // Envelope for smooth sound
                    gainNode.gain.setValueAtTime(0, time);
                    gainNode.gain.linearRampToValueAtTime(this.volume * 0.3, time + 0.01);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, time + note.duration);

                    oscillator.start(time);
                    oscillator.stop(time + note.duration);
                }
                time += note.duration;
            });
        };
    }

    // Play specific notification sound
    play(type = 'message') {
        if (!this.enabled) return;

        if (this.sounds[type]) {
            this.sounds[type]();
        } else {
            console.warn(`Notification sound type "${type}" not found`);
        }
    }

    // Toggle sound on/off
    toggle() {
        this.enabled = !this.enabled;
        localStorage.setItem('notificationSoundsEnabled', this.enabled);
        return this.enabled;
    }

    // Set volume (0.0 to 1.0)
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        localStorage.setItem('notificationVolume', this.volume);
    }

    // Check if sounds are enabled
    isEnabled() {
        return this.enabled;
    }
}

// Create global instance
window.notificationSound = new NotificationSoundManager();

// Helper function for easy access
window.playNotificationSound = (type) => {
    window.notificationSound.play(type);
};
