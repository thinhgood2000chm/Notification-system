pipeline {
        agent any
    stages {
           stage('Build'){

                steps {
                    // This step should not normally be used in your script. Consult the inline help for details.
//                         withDockerRegistry(credentialsId: 'jenkins_docker', url: 'https://index.docker.io/v1/') {
                            sh 'docker login -u thinhnx75 -p thinh54082166'
                            sh 'docker build -t thinhnx75/noti-docker:v1 .'
                            sh 'docker push thinhnx75/noti-docker:v1'
                        }

//                 }
           }

        }
    }

