We are using pipenv to wrap the complexity of the deployment command. The following command will deploy/update the central infrastructure to AWS. All information needed by the python script is found in .env. 

critical:
```powershell
pipenv run deploy
```

This is run automatically upon merge to master