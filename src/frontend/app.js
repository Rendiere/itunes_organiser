const app = Vue.createApp({
    data() {
        return {
            tracks: [],
            uploadProgress: 0,
            uploadStatus: '',
            websocket: null,
            showOnlyMissingYears: false
        }
    },
    computed: {
        filteredTracks() {
            if (this.showOnlyMissingYears) {
                return this.tracks.filter(track => !track.year);
            }
            return this.tracks;
        },
        missingYearsCount() {
            return this.tracks.filter(track => !track.year).length;
        }
    },
    methods: {
        async fetchTracks() {
            try {
                const response = await fetch('/tracks');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                this.tracks = await response.json();
            } catch (error) {
                console.error("Could not fetch tracks:", error);
                alert("Failed to fetch tracks. Please try again.");
            }
        },
        async uploadFile() {
            const file = this.$refs.fileInput.files[0];
            if (!file) {
                alert("Please select a file to upload.");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                this.uploadStatus = `File uploaded successfully. Processing...`;
                
                this.pollUploadProgress(result.task_id);
            } catch (error) {
                console.error("Upload failed:", error);
                this.uploadStatus = "Upload failed. Please try again.";
            }
        },
        pollUploadProgress(taskId) {
            if (this.websocket) {
                this.websocket.close();
            }

            this.websocket = new WebSocket(`ws://${window.location.host}/ws`);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.websocket.send(taskId);
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.status === 'completed') {
                    console.log('Upload and processing completed');
                    this.uploadStatus = `Upload completed! ${data.tracks_created} tracks created.`;
                    this.uploadProgress = 100;
                    this.websocket.close();
                    this.fetchTracks();  // Refresh the track list
                } else if (data.progress) {
                    console.log(`Upload progress: ${data.progress}%`);
                    this.uploadProgress = data.progress;
                    this.uploadStatus = `Processing: ${Math.round(data.progress)}%`;
                }
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.uploadStatus = 'Error during processing. Please try again.';
            };

            this.websocket.onclose = () => {
                console.log('WebSocket closed');
            };
        },
        async inferYearForAll() {
            const tracksWithoutYear = this.tracks.filter(track => !track.year);
            for (const track of tracksWithoutYear) {
                await this.inferYear(track.id);
            }
        },
        async inferYear(trackId) {
            try {
                const response = await fetch(`/infer_year/${trackId}`, { method: 'POST' });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                console.log('Year inference started:', data);
                // You might want to implement progress tracking for year inference as well
            } catch (error) {
                console.error("Year inference failed:", error);
                alert("Failed to start year inference. Please try again.");
            }
        },
        toggleMissingYearsFilter() {
            this.showOnlyMissingYears = !this.showOnlyMissingYears;
        }
    }
});

app.mount('#app');