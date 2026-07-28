let duration = 120;

const timer = document.getElementById("timer");
const resend = document.getElementById("resend-btn");

function updateTimer() {

    const minutes = String(Math.floor(duration / 60)).padStart(2, "0");
    const seconds = String(duration % 60).padStart(2, "0");

    timer.innerHTML = `${minutes}:${seconds}`;

    if (duration <= 0) {

        clearInterval(interval);

        timer.style.display = "none";

        resend.style.display = "inline-block";

        return;
    }

    duration--;

}

updateTimer();

const interval = setInterval(updateTimer, 1000);