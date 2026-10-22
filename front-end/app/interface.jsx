"use client";
import { Mic, StopCircle, Video, Monitor } from 'lucide-react';
import Card from 'react-bootstrap/Card';
import React, { useState, useRef, useEffect } from "react";
// import { initChatModel } from "langchain";

export default function ModelPlayground(){

return (
    <div className="backround_1">
      <div className="backround_2">
        <div className="payground_3"></div>
        {/* <div className="payground_4">
          <HeaderButtons/>
        </div> */}
        <div className="div_1">
          <div className="div_2">
            <h1 className="glow_div">✨</h1>
            <h1 className="h1_gemini_backround">
              Awaken Ambience
            </h1>
          </div>
        </div>

        <div className="div_3">
          <ControlButtons/>
        </div>
      </div>
    </div>
  );
}







function HeaderButtons(){
  return (
    <div className="backround_5">
      <div className="backround_6">
        <button>Logout</button>
      </div>
    </div>
  );
}




function ControlButtons() {
const [chatMode, setChatMode] = useState(null)
const startStream=(stream)=>{
  // alert("Button was clicked!"); // ADD THIS
  if (stream=="chat"){
    setChatMode("chat")
  }else{
    console.log("only chat available")
  }
}

  return (
    <div className='page_layout'>
        <div className="ControlButton_div">
          <button
            className="gimini_1"
            onClick={() => startStream('chat')}
          >
            <Mic className="gimini_2" />
            Start Chatting
          </button>

          <button
            className="gimini_1"
          >
            <Video className="gimini_2" />
            Start Chatting with Video
          </button>
        
          <button
            className="gimini_1"
          >
            <Monitor className="gimini_2" />
            Start Chatting with Screen
          </button>
        

          <button
          variant="destructive"
          className="gimini_1"
          >
          <StopCircle className="gimini_2" />
          Stop Chat
          </button>
        </div>
        <div>
          {chatMode === "chat" && (
            <ChatDisplay/>
          )}
        </div>
    </div>
  );
}



// function llm_generation(){
  
// process.env.OPENAI_API_KEY = "your-api-key";

// const model = await initChatModel("gpt-5.5");
// const response = await model.invoke("Why do parrots talk?");
// }


function ChatDisplay(){
  return(
    <Card className='myCard'>
      <label className="input-container">
        <span className="label-text">System Prompt:</span>
        <input name="myInput" placeholder="no persona pls" className="custom-input" />
      </label>
      <div className='toggle_row'>
        <label className="switch">
          <input type="checkbox"/>
          <span className="slider round"></span>
        </label>
        <span>Enable google search</span>
      </div>
      <label className="input-container">
        <span className="label-text">Generated Output:</span>
        <Card className='generated'>
        <div id="generated-output" className='generated-text'>Generated text</div>
        </Card>
      </label>
    </Card>
  )
}