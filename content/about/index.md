---
title: "about"
layout: "home"
---
{{< details title="What is this for?" closed="false" >}}

This site recommends which NFL games might be enjoyable to watch each week based on data about the games published after they are played. It's geared towards people with full streaming access to all the games at any time.

{{< /details >}}

{{< details title="What do the colours mean?" closed="true" >}}

Red indicates a game probably not worth watching, green indicates a good game, and white indicates a game that doesn't have any data yet.

{{< /details >}}

{{< details title="How does it work?" closed="true" >}}

It pulls information from [nflverse-data](https://github.com/nflverse/nflverse-data) and looks at things like total score, margin of victory, how close the game was in the 4th quarter, and a few other things. It may change as I notice things that could be improved.

{{< /details >}}

{{< details title="How often is it updated?" closed="true" >}}

It gets updated whenever there is fresh data to analyze - typically within a few hours of a game finishing, but occasionally it can be longer.

{{< /details >}}

{{< details title="It seems to pick a pretty wide range of game as \"good\". Why?" closed="true" >}}

If it only picked one type of game (such as high-scoring games with a 3-point or less margin of victory) then it would give away what's going to happen in the game - you'd always know more or less how it was going to end. For the same reason it does not attempt to rank the games it chooses. It simply tries to choose a wide range of what might be enjoyable games to watch so that you'll hopefully get some decent football but still have the enjoyment of watching "live" sports where the outcome is uncertain. Some games will be better than others, but none will be blowouts or field goal snoozefests.

{{< /details >}}
