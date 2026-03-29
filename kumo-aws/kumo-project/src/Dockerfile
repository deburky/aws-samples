FROM public.ecr.aws/lambda/python:3.9

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r requirements.txt

# Copy function code
COPY inference.py ${LAMBDA_TASK_ROOT}

# Copy pre-trained models
# Note: These files must exist or Docker build will fail
# Run 'cd src && python train.py' before building
COPY model.pkl scaler.pkl ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "inference.handler" ]
