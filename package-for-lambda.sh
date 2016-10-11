#!/bin/bash   

# By default lambda-deploy will package the entire folder it is run from and
# upload it to AWS. To keep things a little neater you can run this script to
# copy the Lambda relevant files to a seperate folder then deploy from the new 
# folder.
# 
# Usage
# 
# $ sh package-for-lambda.sh  
# 
# Options
# 
# --name FOLDER_NAME	The name of the folder you want to package into, note
# 						that this will also be the name of the Lambda created 
# 						on AWS. Defaults to kodi-alexa-lambda
# --fresh  				Will remove the package folder and perform a fresh 
# 						install of the requirements.  
# 
# Examples
# 
# $ sh package-for-lambda.sh --name my-app-name 
# $ sh package-for-lambda.sh --fresh 
#  
# 

lambda_dir_name="kodi-alexa-lambda"
frest_start=false

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --name)
    lambda_dir_name="$2"
    shift # past argument
    ;;
    --fresh)
    frest_start=true
    ;;
esac
shift # past argument or value
done

if [ $frest_start == true ]; then
	if [ -d "$lambda_dir_name" ]; then
  		echo " deleting previous folder"
  		rm -rf "$lambda_dir_name"
	else
		echo " no previous folder to delete - check folder name "
		echo " (though might be easier to just delete the folder manually)"
	fi
fi

# Check to see if folder exists 

if [ ! -d "$lambda_dir_name" ]; then
	echo " creating new folder: " . "$lambda_dir_name"
  	mkdir "$lambda_dir_name"
fi

echo " copying relevant files to package folder"
cp .env kodi.py wsgi.py requirements.txt "$lambda_dir_name"

echo " running lambda-deploy deploy"
cd "$lambda_dir_name"

lambda-deploy deploy

exit 0