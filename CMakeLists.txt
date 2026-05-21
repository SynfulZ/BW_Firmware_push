cmake_minimum_required(VERSION 3.16)
project(dummy_firmware LANGUAGES NONE)

add_custom_command(
    OUTPUT ${CMAKE_BINARY_DIR}/firmware.img
    COMMAND ${CMAKE_COMMAND} -E echo "DUMMY_FIRMWARE_IMAGE" > ${CMAKE_BINARY_DIR}/firmware.img
    COMMENT "Generating dummy firmware.img"
)

add_custom_target(firmware ALL
    DEPENDS ${CMAKE_BINARY_DIR}/firmware.img
)
