# Load necessary libraries
library(reticulate)
library(shiny)
library(shinyjs) # For JavaScript integration
library(jsonlite)
library(tictoc)

# Initialize Python environment
use_python("c:/Users/teodo/Documents/R/env/Scripts/python.exe", required = TRUE)

# Import ollama library
ollama <- import("ollama")

# Function to process text with model using ollama.chat
process_with_model <- function(chat_history, max_tokens=2500L) {
  response <- ollama$chat(
    model = "llama3.1:8b-instruct-fp16",
    messages = chat_history
  )
  
  # Debugging: print the entire response object
  print("Response from model:")
  print(response)
  
  if (!is.null(response$message) && !is.null(response$message$content)) {
    return(response$message$content)
  } else {
    return("No response from the model.")
  }
}

# Path to the chat history file
history_file <- "chat_history.json"

# Function to load and fix chat history from disk
load_chat_history <- function(file) {
  if (file.exists(file)) {
    history <- fromJSON(file)
    if (is.data.frame(history)) {
      history <- split(history, seq(nrow(history)))
      history <- lapply(history, as.list)
    }
    # Ensure each element is a list and has the required fields
    fixed_history <- lapply(history, function(msg) {
      if (is.list(msg) && all(c("role", "content") %in% names(msg))) {
        return(msg)
      } else {
        list(role = "system", content = toString(msg))
      }
    })
    # Check for improperly concatenated entries and split them
    final_history <- list()
    for (msg in fixed_history) {
      if (grepl(", ", msg$role) || grepl(", ", msg$content)) {
        roles <- strsplit(msg$role, ", ")[[1]]
        contents <- strsplit(msg$content, ", ")[[1]]
        for (i in seq_along(roles)) {
          final_history <- append(final_history, list(list(role = roles[i], content = contents[i])))
        }
      } else {
        final_history <- append(final_history, list(msg))
      }
    }
    return(final_history)
  } else {
    system_prompt <- list(
      list(role = "system", content = "You are a helpful assistant. You reply with very short answers.")
    )
    return(system_prompt)
  }
}

# Function to save chat history to disk
save_chat_history <- function(history, file) {
  write_json(history, path = file, pretty = TRUE, auto_unbox = TRUE)
}

# Function to validate and correct the chat history structure
validate_chat_history <- function(history) {
  corrected_history <- lapply(history, function(msg) {
    if (is.list(msg) && all(c("role", "content") %in% names(msg))) {
      return(msg)
    } else {
      list(role = "system", content = toString(msg))
    }
  })
  return(corrected_history)
}

# Load chat history
chat_history <- load_chat_history(history_file)
print("Loaded chat history:")  # Debugging: print chat history
print(chat_history)

# Main function to get user input and generate responses
generate_response <- function(user_input, max_tokens = 2500L) {
  # Append the user input to the chat history
  chat_history <<- append(chat_history, list(list(role = "user", content = user_input)))
  
  # Validate chat history structure before sending to API
  chat_history <<- validate_chat_history(chat_history)
  
  # Final validation before sending to API
  chat_history <<- lapply(chat_history, function(msg) {
    if (!is.list(msg) || !all(c("role", "content") %in% names(msg))) {
      stop("Invalid chat history structure before API call")
    }
    return(msg)
  })
  
  # Debugging: print the messages to be sent to the API
  print("Chat history before sending to API:")
  print(chat_history)
  
  # Generate a response using the Ollama model
  tryCatch({
    response_content <- process_with_model(chat_history, max_tokens)
    if (is.null(response_content)) {
      response_content <- "No response from the model."
    }
    
    # Append the response to the chat history
    chat_history <<- append(chat_history, list(list(role = "assistant", content = response_content)))
    
    # Save the chat history to disk
    save_chat_history(chat_history, history_file)
    
    # Print the assistant's response for debugging
    print(paste("Assistant response:", response_content))
    
    return(response_content)
  }, error = function(e) {
    print(paste("Error in generate_response:", e$message))
    return("Error generating response.")
  })
}

# Define the UI for the application
ui <- fluidPage(
  useShinyjs(),  # Initialize shinyjs
  titlePanel("Chatbot"),
  mainPanel(
    tags$head(tags$style(HTML("
      .shiny-input-container { margin-bottom: 0; }
      #chat_output { max-height: 400px; overflow-y: auto; white-space: pre-wrap; width: 90%; }
      #user_input, #send { width: 90%; }
    "))),
    textInput("user_input", "You:", ""),
    actionButton("send", "Send"),
    verbatimTextOutput("chat_output")
  )
)

# Define the server logic
server <- function(input, output, session) {
  # Initialize reactive values for chat history
  chat_history_reactive <- reactiveValues(history = chat_history)
  
  # Observe for Enter key press
  observeEvent(input$user_input, {
    if (!is.null(input$user_input) && input$user_input != "") {
      shinyjs::runjs("
        $('#user_input').keypress(function(e) {
          if(e.which == 13) {
            $('#send').click();
            e.preventDefault();
          }
        });
      ")
    }
  })
  
  # Process the send action
  observeEvent(input$send, {
    user_input <- isolate(input$user_input)
    if (nchar(user_input) > 0) {
      # Generate the response
      response <- generate_response(user_input)
      
      if (!is.null(response)) {
        # Update the reactive chat history
        chat_history_reactive$history <- chat_history
        
        # Update the chat output
        output$chat_output <- renderText({
          chat_lines <- unlist(lapply(chat_history_reactive$history, function(msg) {
            if (!is.list(msg) || !("role" %in% names(msg)) || !("content" %in% names(msg))) {
              stop("Invalid chat history structure")
            }
            paste(msg$role, ": ", msg$content)
          }))
          paste(chat_lines, collapse = "\n")
        })
        
        # Print the response for debugging
        print(paste("Assistant response:", response))
        
        # Scroll to the bottom of the chat output after a delay
        shinyjs::runjs("setTimeout(function() { $('#chat_output').scrollTop($('#chat_output')[0].scrollHeight); }, 100);")
        
        # Clear the user input field
        updateTextInput(session, "user_input", value = "")
      }
    }
  })
  
  # Initialize chat output
  output$chat_output <- renderText({
    chat_lines <- unlist(lapply(chat_history_reactive$history, function(msg) {
      if (!is.list(msg) || !("role" %in% names(msg)) || !("content" %in% names(msg))) {
        stop("Invalid chat history structure")
      }
      paste(msg$role, ": ", msg$content)
    }))
    paste(chat_lines, collapse = "\n")
  })
}

# Run the application
shinyApp(ui = ui, server = server)
