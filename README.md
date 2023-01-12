# KYVE DataPipeline

The KYVE ELT-Pipeline allows developers to connect KYVE to their favorite
data warehouse or destination.

## Quick start

### Starting Airbyte
### Run Airbyte locally

You can run Airbyte locally with Docker.

```bash
git clone https://github.com/KYVENetwork/DataPipeline.git

docker-compose up
```

Login to the web app at [http://localhost:8000](http://localhost:8000) by entering the default credentials found in your .env file.

```
BASIC_AUTH_USERNAME=airbyte
BASIC_AUTH_PASSWORD=password
```

Follow web app UI instructions to set up a source, destination and connection to replicate data. Connections support the most popular sync modes: full refresh, incremental and change data capture for databases.

Read the [Airbyte docs](https://docs.airbyte.com).

### Manage Airbyte configurations with code

Here is a [step-by-step guide](https://github.com/airbytehq/airbyte/tree/e378d40236b6a34e1c1cb481c8952735ec687d88/docs/quickstart/getting-started.md) showing you how to load data from an API into a file, all on your computer.

### Adding the KYVE Source
```bash
cd airbyte-integrations/connectors/source-kyve
docker build . -t airbyte/source-kyve:dev
```

Now visit [http://localhost:8000](http://localhost:8000) and follow [this guide](https://docs.airbyte.com/integrations/custom-connectors/#adding-your-connectors-in-the-ui).