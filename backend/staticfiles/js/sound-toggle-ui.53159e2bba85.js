// Add notification sound toggle to navbar
document.addEventListener('DOMContentLoaded', () => {
    // Find dark mode toggle button
    const darkModeToggle = document.querySelector('button[onclick="toggleDarkMode()"]');

    if (darkModeToggle && darkModeToggle.parentElement) {
        // Create sound toggle button
        const soundToggle = document.createElement('button');
        soundToggle.id = 'sound-toggle';
        soundToggle.className = 'p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition shadow-sm border border-gray-200 dark:border-gray-700';
        soundToggle.title = 'Toggle notification sounds';
        soundToggle.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-eco-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" id="sound-on-icon">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
      </svg>
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400 hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor" id="sound-off-icon">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
      </svg>
    `;

        soundToggle.onclick = () => {
            if (window.notificationSound) {
                const enabled = window.notificationSound.toggle();
                const onIcon = document.getElementById('sound-on-icon');
                const offIcon = document.getElementById('sound-off-icon');

                if (enabled) {
                    onIcon.classList.remove('hidden');
                    offIcon.classList.add('hidden');
                    // Play a test sound
                    window.playNotificationSound('success');
                } else {
                    onIcon.classList.add('hidden');
                    offIcon.classList.remove('hidden');
                }
            }
        };

        // Insert after dark mode toggle
        darkModeToggle.parentElement.insertBefore(soundToggle, darkModeToggle.nextSibling);

        // Initialize state
        if (window.notificationSound && !window.notificationSound.isEnabled()) {
            const onIcon = document.getElementById('sound-on-icon');
            const offIcon = document.getElementById('sound-off-icon');
            if (onIcon && offIcon) {
                onIcon.classList.add('hidden');
                offIcon.classList.remove('hidden');
            }
        }
    }
});
