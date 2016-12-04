#!/bin/bash

cd $1

mkdir 10p
mkdir 240p
mkdir 360p
mkdir 480p
mkdir 720p
mkdir 1080p

ls orig/*|while read i;do gm convert $i -resize "10x" -unsharp 2x0.5+0.5+0 -quality 80 10p/`basename $i`;done
ls orig/*|while read i;do gm convert $i -resize "240x" -unsharp 2x0.5+0.5+0 -quality 80 240p/`basename $i`;done
ls orig/*|while read i;do gm convert $i -resize "360x" -unsharp 2x0.5+0.5+0 -quality 80 360p/`basename $i`;done
ls orig/*|while read i;do gm convert $i -resize "480x" -unsharp 2x0.5+0.5+0 -quality 80 480p/`basename $i`;done
ls orig/*|while read i;do gm convert $i -resize "720x" -unsharp 2x0.5+0.5+0 -quality 80 720p/`basename $i`;done
ls orig/*|while read i;do gm convert $i -resize "1080x" -unsharp 2x0.5+0.5+0 -quality 80 1080p/`basename $i`;done
