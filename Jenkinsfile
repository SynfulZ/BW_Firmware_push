pipeline {
    agent any

    environment {
        // ── Build Target ─────────────────────────────────────────────────────
        BUILD_TARGET   = "8850CM_V1.1_MC661-IN-29-10-JIO"
        OUT_DIR        = "out\\8850CM_V1.1_MC661-IN-29-10-JIO_debug"

        // ── MQTT Config ───────────────────────────────────────────────────────
        MQTT_BROKER    = "broker.hivemq.com"
        MQTT_PORT      = "1883"
        MQTT_TOPIC     = "/bw/mqtt/ota/864071082007457"
        OTA_SEVERITY   = "critical"
        JENKINS_JOB    = "BW_Build_Pipeline"
        NGROK_DOMAIN   = "gleeful-immodest-buckskin.ngrok-free.app"

        // ── Tool Paths ────────────────────────────────────────────────────────
        PYTHON_EXE     = "C:\\Users\\Swastik Sharma\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe"
        GIT_EXE        = "C:\\Users\\Swastik Sharma\\AppData\\Local\\Programs\\Git\\cmd\\git.exe"
        NINJA_EXE      = "C:\\ninja\\ninja.exe"
        TOOLCHAIN      = "gcc-arm-none-eabi-10.2.1"
    }

    stages {

        // ── 0. Validate Tools ─────────────────────────────────────────────────
        stage('Validate Tools') {
            steps {
                script {
                    def tools = [
                        "Python"    : env.PYTHON_EXE,
                        "Git"       : env.GIT_EXE,
                        "Ninja"     : env.NINJA_EXE,
                    ]

                    def missing = []

                    tools.each { name, path ->
                        def exists = bat(
                            script: "if exist \"${path}\" (echo FOUND) else (echo MISSING)",
                            returnStdout: true
                        ).trim()

                        if (exists.contains("FOUND")) {
                            echo "✅ ${name}: ${path}"
                        } else {
                            echo "❌ ${name} not found at: ${path}"
                            missing << name
                        }
                    }

                    // Check arm-none-eabi-gcc via PATH
                    def gccFound = bat(
                        script: "where arm-none-eabi-gcc",
                        returnStdout: true
                    ).trim()

                    if (gccFound) {
                        echo "✅ arm-none-eabi-gcc: ${gccFound}"
                    } else {
                        echo "❌ arm-none-eabi-gcc not found on PATH"
                        missing << "arm-none-eabi-gcc"
                    }

                    if (missing) {
                        error "Missing required tools: ${missing.join(', ')}. Update paths in the environment block at the top of the Jenkinsfile."
                    }
                }
            }
        }

        // ── 1. Checkout ───────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // ── 2. Build ──────────────────────────────────────────────────────────
        stage('Build Firmware') {
            steps {
                bat """
                    call tools\\launch.bat %BUILD_TARGET% debug %TOOLCHAIN%
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

                    cd %OUT_DIR%
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

                    cmake ../.. -G Ninja -DCMAKE_MAKE_PROGRAM=%NINJA_EXE%
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

                    "%NINJA_EXE%"
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
                """
            }
        }

        // ── 3. Compute SHA256 + Version ───────────────────────────────────────
        stage('Compute SHA256 and Version') {
            steps {
                script {
                    def img = bat(
                        script: "dir /s /b %OUT_DIR%\\*.img",
                        returnStdout: true
                    ).trim().readLines().last()

                    echo "Found IMG: ${img}"

                    def certutilOut = bat(
                        script: "certutil -hashfile \"${img}\" SHA256",
                        returnStdout: true
                    ).trim().readLines()

                    def sha = certutilOut[1].trim().toLowerCase()
                    echo "SHA256: ${sha}"

                    def version = bat(
                        script: "\"%GIT_EXE%\" describe --tags --always --dirty",
                        returnStdout: true
                    ).trim().readLines().last()

                    echo "Version: ${version}"

                    def fname = img.tokenize('\\').last()

                    env.IMG_PATH     = img
                    env.IMG_NAME     = fname
                    env.OTA_SHA      = sha
                    env.OTA_VERSION  = version
                    env.FIRMWARE_URL = "http://localhost:8080/job/${env.JENKINS_JOB}/lastSuccessfulBuild/artifact/${env.OUT_DIR}/${fname}"

                    echo "Firmware URL: ${env.FIRMWARE_URL}"
                }
            }
        }

        // ── 4. Archive Firmware ───────────────────────────────────────────────
        stage('Archive Firmware') {
            steps {
                archiveArtifacts artifacts: "out\\8850CM_V1.1_MC661-IN-29-10-JIO_debug\\*.img",
                                 fingerprint: true,
                                 onlyIfSuccessful: true
            }
        }

        // ── 5. Publish OTA via MQTT ───────────────────────────────────────────
     stage('Publish OTA via MQTT') {
    steps {
        script {
            // Start cloudflared tunnel
            bat """
                start /B "%CLOUDFLARED_EXE%" tunnel --url http://localhost:8080 --logfile cloudflared.log
                timeout /t 5
            """

            // Capture tunnel URL
            def tunnelUrl = ""
            def retries = 10

            for (int i = 0; i < retries; i++) {
                sleep(3)
                def tunnelLog = bat(
                    script: "type cloudflared.log",
                    returnStdout: true
                ).trim()

                def match = tunnelLog =~ /https:\/\/[a-z0-9\-]+\.trycloudflare\.com/
                if (match) {
                    tunnelUrl = match[0]
                    echo "✅ Tunnel URL: ${tunnelUrl}"
                    break
                }
                echo "⏳ Waiting for tunnel... attempt ${i + 1}/${retries}"
            }

            if (!tunnelUrl) {
                error "❌ Failed to get tunnel URL from cloudflared"
            }

            // Set firmware URL
            env.FIRMWARE_URL = "${tunnelUrl}/job/${env.JENKINS_JOB}/lastSuccessfulBuild/artifact/${env.OUT_DIR}/${env.IMG_NAME}"
            echo "Firmware URL: ${env.FIRMWARE_URL}"

            // Install paho-mqtt
            bat "\"%PYTHON_EXE%\" -m pip install paho-mqtt --quiet"

            // Write and run publish script
            writeFile file: 'publish_ota.py', text: """
import paho.mqtt.publish as publish
import json, os

payload = json.dumps({
    "version":  os.environ["OTA_VERSION"],
    "url":      os.environ["FIRMWARE_URL"],
    "severity": os.environ["OTA_SEVERITY"],
    "sha":      os.environ["OTA_SHA"]
})

broker = os.environ["MQTT_BROKER"]
port   = int(os.environ["MQTT_PORT"])
topic  = os.environ["MQTT_TOPIC"]

print("OTA Payload : " + payload)
print("Broker      : " + broker + ":" + str(port))
print("Topic       : " + topic)

publish.single(
    topic    = topic,
    payload  = payload,
    hostname = broker,
    port     = port,
    qos      = 1,
    retain   = True
)

print("OTA published successfully.")
"""
            withEnv([
                "OTA_VERSION=${env.OTA_VERSION}",
                "FIRMWARE_URL=${env.FIRMWARE_URL}",
                "OTA_SEVERITY=${env.OTA_SEVERITY}",
                "OTA_SHA=${env.OTA_SHA}",
                "MQTT_BROKER=${env.MQTT_BROKER}",
                "MQTT_PORT=${env.MQTT_PORT}",
                "MQTT_TOPIC=${env.MQTT_TOPIC}"
            ]) {
                bat "\"%PYTHON_EXE%\" publish_ota.py"
            }

            // Keep tunnel alive for 30 minutes
            echo "⏳ Tunnel open for 30 minutes — waiting for soundbox to download firmware..."
            bat "timeout /t 1800 /nobreak"
            bat "taskkill /F /IM cloudflared.exe"
            echo "✅ Tunnel closed."
        }
    }
}

    post {
        success {
            echo "Pipeline completed. Firmware URL: ${env.FIRMWARE_URL}"
        }
        failure {
            echo "Pipeline failed. Check logs above for errors."
        }
    }
}
