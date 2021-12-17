FROM python:3.10

#Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#Set work directory 
WORKDIR /HealthTrace

#Install dependencies
COPY Pipfile Pipfile.lock /HealthTrace/
RUN pip3 install pipenv && pipenv install --system

#Copy project
COPY . /HealthTrace
