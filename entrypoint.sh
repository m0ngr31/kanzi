#!/bin/bash

if [ ! -f ${CONFIG_DIR}/server.crt ]; then
	openssl genrsa -des3 -passout pass:x -out ${CONFIG_DIR}/server.pass.key 2048
	openssl rsa -passin pass:x -in ${CONFIG_DIR}/server.pass.key -out ${CONFIG_DIR}/server.key
	rm ${CONFIG_DIR}/server.pass.key
	openssl req -new -key ${CONFIG_DIR}/server.key -out ${CONFIG_DIR}/server.csr \
		-subj "/C=UK/ST=Warwickshire/L=Leamington/O=OrgName/OU=IT Department/CN=example.com"
	openssl x509 -req -days 365 -in ${CONFIG_DIR}/server.csr -signkey ${CONFIG_DIR}/server.key -out ${CONFIG_DIR}/server.crt
fi

if [ ! -L ${INSTALL_PATH}/kodi.config ]; then
	ln -s ${CONFIG_DIR}/kodi.config ${INSTALL_PATH}/kodi.config
fi

cd ${INSTALL_PATH}
gunicorn --certfile ${CONFIG_DIR}/server.crt --keyfile ${CONFIG_DIR}/server.key --log-level $GUNICORN_LOGLEVEL -b 0.0.0.0:8000 alexa:app

