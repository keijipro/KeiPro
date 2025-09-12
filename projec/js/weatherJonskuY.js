document.addEventListener('DOMContentLoaded', function() {
    console.log("Weather JS loaded for dynamic temperature color.");

    function displayWeather(data) {
        const tempElement = document.querySelector('.weather-info .temperature');
        if (tempElement) {
            tempElement.textContent = `${data.temperature}°C`;
            updateTemperatureColor('.weather-info .temperature');
        }

        const conditionElement = document.querySelector('.weather-info .condition');
        if (conditionElement) {
            conditionElement.textContent = data.condition;
        }

        const locationElement = document.querySelector('.weather-info .location');
        if (locationElement) {
            locationElement.textContent = data.location; // Memperbarui elemen lokasi
        }
    }


    function updateWeather(latitude, longitude) {
        fetch(`/api/get_weather?lat=${latitude}&lon=${longitude}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error("Error from Flask backend:", data.error);
                    document.querySelector('.weather-info .temperature').textContent = '--°C';
                    document.querySelector('.weather-info .condition').textContent = 'Error!';
                    document.querySelector('.weather-info .location').textContent = data.error;
                    return;
                }
                displayWeather(data);
            })
            .catch(error => {
                console.error("Failed to fetch weather data:", error);
                document.querySelector('.weather-info .temperature').textContent = '--°C';
                document.querySelector('.weather-info .condition').textContent = 'Gagal';
                document.querySelector('.weather-info .location').textContent = 'Memuat Cuaca';
            });
    }

    function getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    console.log(`Lokasi didapat: Lat ${latitude}, Lon ${longitude}`);
                    updateWeather(latitude, longitude);
                },
                error => {
                    console.error("Gagal mendapatkan lokasi:", error);
                    const fallbackCity = document.body.dataset.defaultCity;
                    if (fallbackCity) {
                        console.log(`Mencoba cuaca untuk kota default: ${fallbackCity}`);
                        fetch(`/api/get_weather?city=${fallbackCity}`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    console.error("Error with fallback city:", data.error);
                                    document.querySelector('.weather-info .temperature').textContent = '--°C';
                                    document.querySelector('.weather-info .condition').textContent = 'Error!';
                                    document.querySelector('.weather-info .location').textContent = data.error;
                                    return;
                                }
                                displayWeather(data);
                            })
                            .catch(err => {
                                console.error("Failed to fetch fallback weather:", err);
                                document.querySelector('.weather-info .temperature').textContent = '--°C';
                                document.querySelector('.weather-info .condition').textContent = 'Gagal';
                                document.querySelector('.weather-info .location').textContent = 'Memuat Cuaca';
                            });
                    } else {
                        console.log("Tidak ada kota default yang dikonfigurasi.");
                        document.querySelector('.weather-info .temperature').textContent = '--°C';
                        document.querySelector('.weather-info .condition').textContent = 'No Data';
                        document.querySelector('.weather-info .location').textContent = 'Admin Belum Atur Kota';
                    }
                }
            );
        } else {
            console.error("Geolocation tidak didukung oleh browser ini.");
            const fallbackCity = document.body.dataset.defaultCity;
            if (fallbackCity) {
                console.log(`Mencoba cuaca untuk kota default (browser tidak support geolocation): ${fallbackCity}`);
                fetch(`/api/get_weather?city=${fallbackCity}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            console.error("Error with fallback city:", data.error);
                            document.querySelector('.weather-info .temperature').textContent = '--°C';
                            document.querySelector('.weather-info .condition').textContent = 'Error!';
                            document.querySelector('.weather-info .location').textContent = data.error;
                            return;
                        }
                        displayWeather(data);
                    })
                    .catch(err => {
                        console.error("Failed to fetch fallback weather:", err);
                        document.querySelector('.weather-info .temperature').textContent = '--°C';
                        document.querySelector('.weather-info .condition').textContent = 'Gagal';
                        document.querySelector('.weather-info .location').textContent = 'Memuat Cuaca';
                    });
            } else {
                console.log("Tidak ada kota default yang dikonfigurasi dan geolocation tidak didukung.");
                document.querySelector('.weather-info .temperature').textContent = '--°C';
                document.querySelector('.weather-info .condition').textContent = 'No Data';
                document.querySelector('.weather-info .location').textContent = 'Admin Belum Atur Kota';
            }
        }
    }

    function updateTemperatureColor(tempElementSelector) {
        const tempElement = document.querySelector(tempElementSelector);
        if (!tempElement) return;

        const tempText = tempElement.textContent.replace('°C', '').trim();
        const temperature = parseFloat(tempText);

        if (isNaN(temperature)) return;

        tempElement.classList.remove('hot', 'warm', 'cool', 'cold');
        if (temperature >= 33) {
            tempElement.classList.add('hot');
        } else if (temperature >= 30 && temperature < 33) {
            tempElement.classList.add('warm');
        } else if (temperature >= 27 && temperature < 30) {
            tempElement.classList.add('cool');
        } else {
            tempElement.classList.add('cold');
        }
    }

    getUserLocation();
});
