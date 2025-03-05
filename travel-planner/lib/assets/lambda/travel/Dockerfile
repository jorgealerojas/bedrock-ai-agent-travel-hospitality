FROM public.ecr.aws/lambda/python:3.9.2024.03.04.10-x86_64

# Install python and dependencies
RUN yum update -y && \
    yum install -y python3 python3-dev python3-pip gcc && \
    rm -Rf /var/cache/yum

# Copy and install requirements
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the travel agent function
COPY agent.py ./

# Set the handler
CMD ["agent.lambda_handler"] 