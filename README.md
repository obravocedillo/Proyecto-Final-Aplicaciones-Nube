-Descripción: AplicacIón hecha en Flask con python en la cual se pueden aplicar filtros a imagenes, guardarlas y descargarlas.

-Se tiene que estar dentro de una carpeta llamada mpi-cluster

-Demo: https://youtu.be/PaRoU1cg1aM

-GitHub: https://github.com/obravocedillo/Proyecto-Final-Aplicaciones-Nube

-Docker: gcr.io/inbound-footing-274623/mpi-docker-proyecto


-Comandos usados

docker build -t mpi-docker-proyecto .
docker tag  mpi-docker-proyecto gcr.io/inbound-footing-274623/mpi-docker-proyecto
docker push gcr.io/inbound-footing-274623/mpi-docker-proyecto
kubectl apply -f deployment.yaml
chmod +x pod_copy.sh
./pod_copy.sh
kubectl get pods
kubectl exec [pod] -- mpiexec -f hosts -n 2 python3 example.py

-Borrar deploy

kubectl delete deploy mpi-docker 

-ver servicios

kubectl get services

-Mandar archivo a todos los pods

for podname in $(kubectl get pods -o json| jq -r '.items[].metadata.name'); do kubectl cp example.py  ${podname}:/mpi/; done
