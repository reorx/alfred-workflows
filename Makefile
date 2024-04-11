all: devdocs ghdev

devdocs:
	bash sync-source.sh 7CD67814-44A1-4E5B-9AE0-5413FE1860E7 devdocs

ghdev:
	bash sync-source.sh 28E8088D-B16D-4D33-A224-B8D335FA9923 ghdev
