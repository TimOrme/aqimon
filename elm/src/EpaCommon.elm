module EpaCommon exposing (..)


type EpaLevel
    = Hazardous
    | VeryUnhealthy
    | Unhealthy
    | UnhealthyForSensitive
    | Moderate
    | Good


getColorForLevel : EpaLevel -> String
getColorForLevel level =
    case level of
        Hazardous ->
            "maroon"

        VeryUnhealthy ->
            "purple"

        Unhealthy ->
            "red"

        UnhealthyForSensitive ->
            "orange"

        Moderate ->
            "yellow"

        Good ->
            "green"


getLabelForLevel : EpaLevel -> String
getLabelForLevel level =
    case level of
        Hazardous ->
            "Hazardous"

        VeryUnhealthy ->
            "Very Unhealthy"

        Unhealthy ->
            "Unhealthy"

        UnhealthyForSensitive ->
            "Unhealthy For Sensitive"

        Moderate ->
            "Moderate"

        Good ->
            "Good"
