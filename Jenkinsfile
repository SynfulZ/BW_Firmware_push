pipeline {
    agent any

    environment {
        BUILD_TARGET   = "8850CM_V1.1_MC661-IN-29-10-JIO"
        OUT_DIR        = "out\\8850CM_V1.1_MC661-IN-29-10-JIO_debug"
        MQTT_BROKER    = "broker.hivemq.com"
        MQTT_PORT      = "1883"
        MQTT_TOPIC     = "/bw/mqtt/ota/864071082007457"
        OTA_SEVERITY   = "critical"
        JENKINS_JOB    = "BW_Build_Pipeline"
        NGROK_DOMAIN   = "gleeful-immodest-buckskin.ngrok-free.app"
    }

    stages {

        // ── 1. Checkout ──────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // ── 2. Build ─────────────────────────────────────────────────────────
        stage('Build Firmware') {
            steps {
                bat 'where arm-none-eabi-gcc'
                bat """
                    set PATH=C:\\ninja;C:\\Program Files (x86)\\Arm\\GNU Toolchain mingw-w64-i686-arm-none-eabi\\bin;%PATH%

                    call tools\\launch.bat %BUILD_TARGET% debug gcc-arm-none-eabi-10.2.1
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

                    set BUILD_TARGET=%BUILD_TARGET%

                    cd %OUT_DIR%
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

                    cmake ../.. -G Ninja
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

                    ninja
                    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
                """
            }
        }

        // ── 3. Compute SHA256 + version ──────────────────────────────────────
        stage('Compute SHA256 and Version') {
            steps {
                script {
                    def img = bat(
                        script: "dir /s /b %OUT_DIR%\\*.img",
                        returnStdout: true
                    ).trim().readLines().last()

                    echo "Found IMG: ${img}"

                    def sha = bat(
                        script: "certutil -hashfile \"${img}\" SHA256 | findstr /v hash | findstr /v CertUtil",
                        returnStdout: true
                    ).trim().replaceAll("\\s", "").toLowerCase()

                    echo "SHA256: ${sha}"

                    def version = bat(
                        script: "git describe --tags --always --dirty",
                        returnStdout: true
                    ).trim().readLines().last()

                    echo "Version: ${version}"

                    def fname = img.tokenize('\\').last()

                    env.IMG_PATH     = img
                    env.IMG_NAME     = fname
                    env.OTA_SHA      = sha
                    env.OTA_VERSION  = version
                    env.FIRMWARE_URL = "https://${env.NGROK_DOMAIN}/job/${env.JENKINS_JOB}/lastSuccessfulBuild/artifact/${env.OUT_DIR}/${fname}"

                    echo "Firmware URL: ${env.FIRMWARE_URL}"
                }
            }
        }

        // ── 4. Archive .img as Jenkins artifact ──────────────────────────────
        stage('Archive Firmware') {
            steps {
                archiveArtifacts artifacts: "out\\8850CM_V1.1_MC661-IN-29-10-JIO_debug\\*.img",
                                 fingerprint: true,
                                 onlyIfSuccessful: true
            }
        }

        // ── 5. Publish OTA JSON to HiveMQ ────────────────────────────────────
        stage('Publish OTA via MQTT') {
            steps {
                script {
                    bat "pip install paho-mqtt --quiet"

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
                        bat "python publish_ota.py"
                    }
                }
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
