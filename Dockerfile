FROM python:3.10

#Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#Set work directory 
WORKDIR /POLICE_AUCTION

#Install dependencies
COPY Pipfile Pipfile.lock /POLICE_AUCTION/
RUN pip3 install pipenv && pipenv install --system

#Copy project
COPY . /POLICE_AUCTION