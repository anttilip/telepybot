#!/bin/bash

# gm mogrify needs to be called from folder where images are
cd $1/orig

# Convert all images to their own folders, 10p needs to be converted to png
gm mogrify -output-directory ../10p -create-directories -format png -resize 10x *
gm mogrify -output-directory ../240p -create-directories -resize 240x * -unsharp 2x0.5+0.5+0 -quality 80
gm mogrify -output-directory ../360p -create-directories -resize 360x * -unsharp 2x0.5+0.5+0 -quality 80
gm mogrify -output-directory ../480p -create-directories -resize 480x * -unsharp 2x0.5+0.5+0 -quality 80
gm mogrify -output-directory ../720p -create-directories -resize 720x * -unsharp 2x0.5+0.5+0 -quality 80
gm mogrify -output-directory ../1080p -create-directories -resize 1080x * -unsharp 2x0.5+0.5+0 -quality 80
