const startRecordingButton = document.getElementById('startRecording');
const stopRecordingButton = document.getElementById('stopRecording');

let mediaRecorder;
let chunks = [];

startRecordingButton.addEventListener('click', startRecording);
stopRecordingButton.addEventListener('click', stopRecording);

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.addEventListener('dataavailable', event => {
            chunks.push(event.data);
        });
        
        mediaRecorder.addEventListener('stop', () => {
            const blob = new Blob(chunks, { type: 'audio/wav' });
            sendAudioData(blob);
            chunks = [];
        });
        
        mediaRecorder.start();
    } catch (error) {
        console.error('Error starting recording:', error);
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

async function sendAudioData(blob) {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.wav');
    
    try {
        const response = await fetch('/process_audio', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            console.log('Audio data sent successfully');
        } else {
            console.error('Failed to send audio data:', response.statusText);
        }
    } catch (error) {
        console.error('Error sending audio data:', error);
    }
}
