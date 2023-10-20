function goToChat(username) {
    window.location = '/chat/' + username;
  }

  document.addEventListener('DOMContentLoaded', function() {
    var socket = io();

    socket.on('connect', function() {
      console.log('Connected to the server');
    });

    socket.on('message', function(data) {
      var message = data.msg;
      var timestamp = data.timestamp;
      display_left(message, timestamp);
    });
    socket.on('message1', function(data) {
      display_right(message, timestamp);
    });

    document.getElementById('messageForm').addEventListener('submit', function(event) {
      event.preventDefault();
      var message = document.getElementById('input').value;
      if (message.trim() === "") {
        return;
      }
      recipient = document.getElementById('name').textContent;
      socket.emit('message', { msg: message, recipient: recipient });
      var currentDateTime = new Date();
      var year = currentDateTime.getFullYear();
      var month = currentDateTime.getMonth() + 1; // getMonth() returns a zero-based value (0-11)
      var day = currentDateTime.getDate();
      var hours = currentDateTime.getHours();
      var mins = currentDateTime.getMinutes();
      var secs = currentDateTime.getSeconds();
      var time = year + "-" + month + "-" + day + " " + hours + ":" + mins + ":" + secs;
      display_left(message, time)
      document.getElementById('input').value = '';
    });

    function display_right(message, time) {
      $('#chat').append('<p class="chatright">' + message + '</div>');
      $('#chat').append('<p class="infol">' + time + '</div>');
    }
    function display_left(message, time){
      $('#chat').append('<div class="chatleft">' + message + '</div>');
      $('#chat').append('<p class="infor">' + time + '</div>');
    }
  });