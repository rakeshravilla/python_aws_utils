#!/bin/sh

echo "Enter your client name: "; read -r client_name

if [ ! -f "${client_name}_pipelines.txt" ]; then
        echo "Pipeline file not found for client $client_name!"
        exit 1
fi

echo "Which env you are running? uat, sit, ppr?? - "; read -r ENV
ENV=$(echo "$ENV" | tr '[:lower:]' '[:upper:]')

echo "Which phase of pipelines do you want to run?? Enter number between 1-9!! - "; read -r NUM
echo "Running the phase ${NUM} of pipelines"

pipelines=$(grep "^$NUM:" "${client_name}_pipelines.txt" | cut -d ":" -f 2)

echo "Please enter date in yyyyMMdd format : "; read -r DATE
DATE=$(echo "$DATE" | awk '{print substr($0, 1, 4) "-" substr($0, 5, 2) "-" substr($0, 7, 2)}')
echo "Please enter date in HH:MM format : "; read -r TIME
if [ -z "$TIME" ]; then
  TIME="18:00"
fi
echo "Date and Time is set to ${DATE}-${TIME}"

for pipeline in $pipelines
do
  pipeline="${ENV}_${pipeline}"
  echo "$pipeline"
  cmd=$(aws lambda invoke --function-name InboundFileHandler_"$ENV"_dataPipelineTriggerHandler \
      --log-type Tail --payload "{
          \"time\": \"${DATE}T${TIME}:00Z\",
          \"detail\": {
              \"pipelinesToRunByName\": \"$pipeline\"
          }
      }" --color auto --query 'LogResult' out --output text |  base64 -d)

  mkdir -p .output && echo "$cmd" > .output/"$pipeline".txt

  echo -e "\e[33mPipeline triggering started\e[0m"

  if echo "$cmd" | grep -q "ActivationSuccess"; then
     echo -e "\e[1;32mActivationSuccess\e[0m - $pipeline"
  elif echo "$cmd" | grep -q "ActivationNone"; then
     echo -e "\e[1;31mPipeline - $pipeline - not triggered\e[0m"
  else
     echo -e "\e[1;31mData pipeline trigger lambda failed for - $pipeline\e[0m"
  fi
  echo -e "\e[33mPipeline triggering end\e[0m"
done