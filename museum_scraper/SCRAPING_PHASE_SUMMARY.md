Summary for your main project chat

You can paste the following into your main classifier/UI chat.

Artifact Identifier Project – Scraping Phase Summary
Objective

The goal of the scraping phase was to build an offline artifact information database for the AI Artifact Identifier project.

Instead of querying the internet during prediction, the project now stores official museum information locally.

The source used is the Museums of India – Archaeological Survey of India (Goa Museum) repository.

Museum Website

Source:

https://museumsofindia.gov.in/repository/collection/ObjectType?museum=gom_goa

Only these categories were targeted:

Sculpture
Architecture
Arm (to be scraped later using the same scraper)
Reverse Engineering

Using Chrome Developer Tools (Network tab), the website API was analyzed.

The following endpoints were identified.

Category List
fetchCategories

Used only to determine available categories.

Artifact List
fetchRecords

Returns

recordIdentifier
title
short description
museum
image reference

This endpoint was used for pagination.

Artifact Detail Page

Each artifact has an individual page

https://museumsofindia.gov.in/repository/record/<recordIdentifier>

This page contains the complete metadata.

Images

Initially the API returned obsolete image URLs

http:///museumsofindia.gov.in:81/...

These URLs were broken.

After inspecting browser requests, the correct image endpoint was discovered:

https://museumsofindia.gov.in/repository/file/
<museum>/<recordIdentifier>/<recordIdentifier>_01_l.jpg

The scraper automatically downloaded every available image for every artifact.

Image Scraper

Implemented:

automatic pagination
downloads all Sculpture records
downloads all available images
cleans HTML descriptions
creates one folder per artifact title

Folder structure:

museum_data/

    sculpture/

        Hero Stone/

        Bhairava/

        Vishnu Dashavathara on Prabhavli/

        ...

Each folder contains

images
info.json
Metadata Scraper

A second scraper was developed.

It visits every artifact page individually.

For each record it extracts all available museum information.

The final JSON keeps only these fields.

{
    "title": "",
    "object_type": "",
    "main_material": "",
    "provenance": "",
    "style": "",
    "period": "",
    "tribe": "",
    "culture": "",
    "brief_description": "",
    "detailed_description": ""
}

The scraper successfully processed

193 museum records

Result

Matched : 193
Skipped : 0
Failed : 0
Why only 144 folders?

The museum database contains

193 records

but only about

144 unique artifact titles

Example

Hero Stone
Hero Stone
Hero Stone
Hero Stone

These represent different museum objects having the same title.

For the AI project, one folder per artifact title is sufficient because the classifier predicts the artifact class, not the museum accession number.

Folder Cleanup

Folders were renamed

Hero_Stone

↓

Hero Stone

to match future dataset class names.

JSON Cleanup

The original museum metadata was simplified into the required format.

Only useful fields were retained.

Every artifact folder now contains

info.json

with the cleaned metadata.

Generated Files

Generated

artifact_classes.txt

Contains every final artifact class.

One class per line.

Used later while updating the CNN dataset.

Generated

artifact_database.json

Contains every artifact and its cleaned metadata.

Example

{
    "Hero Stone": {
        ...
    },

    "Bhairava": {
        ...
    }
}

This file can later be loaded directly by Flask.

Final Dataset Structure
museum_data/

    sculpture/

        Hero Stone/

            Hero Stone_1.jpg
            Hero Stone_2.jpg
            ...

            info.json

        Bhairava/

            Bhairava_1.jpg
            ...

            info.json

        ...

artifact_classes.txt

artifact_database.json
Planned Integration

During prediction

CNN predicts class

↓

Confidence > threshold

↓

Predicted class name

↓

Load corresponding data

↓

Display artifact information

The website will display

Artifact Name
Category
Material
Period
Style
Tribe
Culture
Brief Description
Detailed Description
Related Images

No internet connection is required because all information is stored locally.