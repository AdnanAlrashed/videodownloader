// $('#infoForm').on('submit', function(event) {
//     event.preventDefault();
//     var url = $('#video_url').val();
//     $.ajax({
//         type: 'POST',
//         url: $(this).attr('action'),
//         data: {
//             'video_url': url,
//             'csrfmiddlewaretoken': '{{ csrf_token }}'
//         },
//         success: function(response) {
//             if (response.error) {
//                 Swal.fire({
//                     icon: 'error',
//                     title: 'Oops...',
//                     text: response.error,
//                 });
//                 return;
//             }
//             $('#video-info').show();
//             $('#title').html('Title: ' + response.title);
//             $('#uploader').html('Uploader: ' + response.uploader);
//             $('#duration').html('Duration: ' + (response.duration / 60).toFixed(2) + ' minutes');
//             $('#thumbnail').attr('src', response.thumbnail);
//             $('#hidden_video_url').val(url);
            
//             if (response.video_url) {
//                 $('#thumbnail').data('video-url', response.video_url);
//             }
//         },
//         error: function(xhr, status, error) {
//             Swal.fire({
//                 icon: 'error',
//                 title: 'Oops...',
//                 text: 'An error occurred: ' + error,
//             });
//         }
//     });
// });


// $('#downloadForm').on('submit', function(event) {
//     event.preventDefault();
//     var formData = $(this).serialize();
//     $('.progress').show();
//     $.ajax({
//         type: 'POST',
//         url: $(this).attr('action'),
//         data: formData,
//         success: function(response) {
//             if (response.finished) {
//                 Swal.fire({
//                     icon: 'success',
//                     title: 'Download Complete!',
//                     text: response.finished,
//                     showConfirmButton: false,
//                     timer: 1500
//                 });
//                 $('.progress-bar').addClass('progress-bar-success').css('width', '100%').attr('aria-valuenow', 100);
//             } else if (response.error) {
//                 Swal.fire({
//                     icon: 'error',
//                     title: 'Oops...',
//                     text: response.error,
//                 });
//             }
//             $('.progress').hide();
//         },
//         error: function(xhr, status, error) {
//             Swal.fire({
//                 icon: 'error',
//                 title: 'Oops...',
//                 text: 'An error occurred: ' + error,
//             });
//             $('.progress').hide();
//         },
//         xhr: function() {
//             var xhr = new window.XMLHttpRequest();
//             xhr.upload.addEventListener('progress', function(e) {
//                 if (e.lengthComputable) {
//                     var percentComplete = (e.loaded / e.total) * 100;
//                     $('.progress-bar').css('width', percentComplete + '%').attr('aria-valuenow', percentComplete);
//                 }
//             });
//             return xhr;
//         }
//     });
// });

//  // Handle thumbnail click event
//  $('#thumbnail').on('click', function() {
//     var videoUrl = $(this).data('video-url');
//     if (videoUrl) {
//         var videoPlayer = $('#video-preview');
//         videoPlayer.attr('src', videoUrl).fadeIn().show();
//         videoPlayer[0].load();
//         videoPlayer[0].play();
//     }
// });
// // document.getElementById('download-form').addEventListener('submit', function(e) {
// //     e.preventDefault(); // منع التحميل الافتراضي للاستمارة

// //     const progressBar = document.getElementById('progress-bar');
// //     progressBar.style.width = '0%';
// //     progressBar.setAttribute('aria-valuenow', 0);
// //     progressBar.textContent = '0%';

// //     const xhr = new XMLHttpRequest();
// //     xhr.open('POST', this.action, true);
// //     xhr.setRequestHeader('X-CSRFToken', document.querySelector('input[name="csrfmiddlewaretoken"]').value);

// //     xhr.upload.onprogress = function(e) {
// //         if (e.lengthComputable) {
// //             const percentComplete = (e.loaded / e.total) * 100;
// //             progressBar.style.width = percentComplete + '%';
// //             progressBar.setAttribute('aria-valuenow', percentComplete);
// //             progressBar.textContent = Math.round(percentComplete) + '%';
// //         }
// //     };

// //     xhr.onload = function() {
// //         if (xhr.status === 200) {
// //             try {
// //                 const response = JSON.parse(xhr.responseText);
// //                 if (response.status === 'success') {
// //                     progressBar.style.width = '100%';
// //                     progressBar.setAttribute('aria-valuenow', 100);
// //                     progressBar.textContent = 'Download complete!';
// //                 } else {
// //                     progressBar.style.width = '100%';
// //                     progressBar.setAttribute('aria-valuenow', 100);
// //                     progressBar.textContent = 'Download failed!';
// //                 }
// //             } catch (e) {
// //                 console.error('Parsing error:', e); // Print parsing error details
// //                 progressBar.style.width = '100%';
// //                 progressBar.setAttribute('aria-valuenow', 100);
// //                 progressBar.textContent = 'Error occurred!';
// //             }
// //         } else {
// //             console.error('HTTP error:', xhr.status, xhr.statusText); // Print HTTP error details
// //             progressBar.style.width = '100%';
// //             progressBar.setAttribute('aria-valuenow', 100);
// //             progressBar.textContent = 'Download failed!';
// //         }
// //     };

// //     xhr.onerror = function() {
// //         console.error('Request error'); // Print request error details
// //         progressBar.style.width = '100%';
// //         progressBar.setAttribute('aria-valuenow', 100);
// //         progressBar.textContent = 'Error occurred!';
// //     };

// //     xhr.send(new FormData(this));
// // });
