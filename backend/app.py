from flask import Flask, render_template, redirect, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import flask_cors
import re
import random
import json
import logging
from datetime import datetime

from gemini import chat_session

app = Flask(__name__)
flask_cors.CORS(app)

# Fallback quiz data for different topics
FALLBACK_QUIZZES = {
    "climate": {
        "questions": [
            {
                "question": "What is the main greenhouse gas contributing to climate change?",
                "options": ["Carbon dioxide", "Helium", "Neon", "Hydrogen"],
                "correct_answer": 0
            },
            {
                "question": "Which human activity releases the most greenhouse gases?",
                "options": ["Burning fossil fuels", "Swimming", "Reading", "Playing sports"],
                "correct_answer": 0
            }
        ]
    },
    "default": {
        "questions": [
            {
                "question": "Which environmental issue is most pressing?",
                "options": ["Climate change", "Pollution", "Deforestation", "All of the above"],
                "correct_answer": 3
            }
        ]
    }
}


def extract_json_content(text):
    """
    Extract valid JSON content from text using multiple approaches
    """
    try:
        # First attempt: Try to find JSON between code blocks
        json_matches = re.findall(r'```(?:json)?\s*({[\s\S]*?})\s*```', text)
        if json_matches:
            for match in json_matches:
                try:
                    return json.loads(match)
                except:
                    continue

        # Second attempt: Find any JSON-like structure
        json_matches = re.findall(r'{[\s\S]*?}', text)
        if json_matches:
            for match in json_matches:
                try:
                    return json.loads(match)
                except:
                    continue

        # Third attempt: Try to construct valid JSON from the text
        questions = []
        current_question = {}

        # Look for question patterns
        question_matches = re.finditer(r'["\']question["\']\s*:\s*["\']([^"\']+)["\']', text)
        options_matches = re.finditer(r'["\']options["\']\s*:\s*\[(.*?)\]', text)
        answer_matches = re.finditer(r'["\']correct_answer["\']\s*:\s*(\d+)', text)

        for q, o, a in zip(question_matches, options_matches, answer_matches):
            try:
                # Clean and parse options
                options_str = o.group(1)
                options = re.findall(r'["\']([^"\']+)["\']', options_str)

                if len(options) == 4:  # Only add if we have exactly 4 options
                    questions.append({
                        "question": q.group(1),
                        "options": options,
                        "correct_answer": int(a.group(1))
                    })
            except:
                continue

        if questions:
            return {"questions": questions}

    except Exception as e:
        app.logger.error(f"JSON extraction error: {str(e)}")
        return None

    return None


def get_fallback_quiz(topic):
    """Get appropriate fallback quiz based on topic and randomly select 5 questions"""
    topic = topic.lower()
    fallback_quizzes = {
        "deforestation": {
            "questions": [
                {
                    "question": "What is the primary driver of global deforestation?",
                    "options": ["Agriculture expansion", "Urban development", "Mining", "Logging"],
                    "correct_answer": 0
                },
                {
                    "question": "Which region has the highest rate of deforestation?",
                    "options": ["Amazon Rainforest", "Congo Basin", "Southeast Asia", "Central America"],
                    "correct_answer": 0
                },
                {
                    "question": "What percentage of Earth's original forests have been lost?",
                    "options": ["46%", "31%", "25%", "52%"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the main impact of deforestation on biodiversity?",
                    "options": ["Habitat loss", "Soil erosion", "Climate change", "Water pollution"],
                    "correct_answer": 0
                },
                {
                    "question": "How many acres of forest are lost every minute globally?",
                    "options": ["30 acres", "20 acres", "40 acres", "50 acres"],
                    "correct_answer": 0
                },
                {
                    "question": "What is REDD+?",
                    "options": ["Reducing Emissions from Deforestation and Forest Degradation",
                                "Reforestation Economic Development Deal", "Regional Environmental Defense Division",
                                "Rainforest Ecosystem Development Database"],
                    "correct_answer": 0
                },
                {
                    "question": "What percentage of greenhouse gas emissions are caused by deforestation?",
                    "options": ["15%", "5%", "25%", "35%"],
                    "correct_answer": 0
                },
                {
                    "question": "Which industry is most responsible for tropical deforestation?",
                    "options": ["Cattle ranching", "Palm oil", "Timber", "Mining"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the most effective solution to combat deforestation?",
                    "options": ["Sustainable forest management", "Complete logging ban",
                                "Urban development restriction", "Increased mining regulations"],
                    "correct_answer": 0
                },
                {
                    "question": "How does deforestation affect local communities?",
                    "options": ["Loss of livelihood and resources", "Improved economic opportunities",
                                "Better access to urban areas", "Increased agricultural land"],
                    "correct_answer": 0
                }
            ]
        },
        "climate change": {
            "questions": [
                {
                    "question": "What is the main greenhouse gas contributing to climate change?",
                    "options": ["Carbon dioxide", "Methane", "Water vapor", "Nitrous oxide"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the Paris Agreement's main goal?",
                    "options": ["Limit global temperature rise to 1.5°C-2°C", "Ban fossil fuels",
                                "Protect endangered species", "Reduce ocean pollution"],
                    "correct_answer": 0
                },
                {
                    "question": "Which sector produces the most greenhouse gas emissions globally?",
                    "options": ["Energy production", "Agriculture", "Transportation", "Manufacturing"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the greenhouse effect?",
                    "options": ["Trapping of heat by atmospheric gases", "Plant growth in greenhouses",
                                "Ozone depletion", "Arctic ice melting"],
                    "correct_answer": 0
                },
                {
                    "question": "What is a carbon footprint?",
                    "options": ["Total greenhouse gases produced by human activities",
                                "Physical impression left by carbon", "Carbon dioxide in the atmosphere",
                                "Carbon-based fuel usage"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the IPCC?",
                    "options": ["Intergovernmental Panel on Climate Change",
                                "International Protocol for Climate Control",
                                "Institute for Planetary Climate Conservation",
                                "Industrial Partnership for Climate Cooperation"],
                    "correct_answer": 0
                },
                {
                    "question": "What is carbon sequestration?",
                    "options": ["Process of capturing and storing carbon dioxide", "Carbon dioxide production",
                                "Carbon-based fuel extraction", "Carbon molecule splitting"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the urban heat island effect?",
                    "options": ["Cities being warmer than surrounding areas", "Tropical islands in cities",
                                "Heat waves in urban areas", "City-based greenhouse effect"],
                    "correct_answer": 0
                },
                {
                    "question": "What is climate mitigation?",
                    "options": ["Actions to reduce greenhouse gas emissions", "Adapting to climate change",
                                "Weather prediction", "Temperature measurement"],
                    "correct_answer": 0
                },
                {
                    "question": "What role do oceans play in climate change?",
                    "options": ["Absorb heat and carbon dioxide", "Produce greenhouse gases",
                                "Increase global temperature", "Generate wind patterns"],
                    "correct_answer": 0
                }
            ]
        },
        "social displacement": {
            "questions": [
                {
                    "question": "What is a climate refugee?",
                    "options": ["Person displaced by climate-related disasters", "Environmental scientist",
                                "Climate change activist", "Weather forecaster"],
                    "correct_answer": 0
                },
                {
                    "question": "Which region is most affected by climate-induced migration?",
                    "options": ["Pacific Islands", "Northern Europe", "Central Canada", "Southern Argentina"],
                    "correct_answer": 0
                },
                {
                    "question": "What is environmental justice?",
                    "options": ["Fair treatment regarding environmental impacts", "Environmental law enforcement",
                                "Nature conservation", "Wildlife protection"],
                    "correct_answer": 0
                },
                {
                    "question": "How does climate change affect indigenous communities?",
                    "options": ["Loss of traditional territories and practices", "Increased technological advancement",
                                "Better access to resources", "Improved living conditions"],
                    "correct_answer": 0
                },
                {
                    "question": "What percentage of global migration is influenced by climate change?",
                    "options": ["20%", "5%", "50%", "75%"],
                    "correct_answer": 0
                },
                {
                    "question": "Which natural disaster causes the most displacement?",
                    "options": ["Floods", "Earthquakes", "Volcanic eruptions", "Landslides"],
                    "correct_answer": 0
                },
                {
                    "question": "What is managed retreat?",
                    "options": ["Planned relocation from high-risk areas", "Military strategy", "Wildlife migration",
                                "Forest management"],
                    "correct_answer": 0
                },
                {
                    "question": "How does climate displacement affect urban areas?",
                    "options": ["Increased pressure on infrastructure and services", "Reduced population density",
                                "Better urban planning", "Decreased housing demand"],
                    "correct_answer": 0
                },
                {
                    "question": "What is climate gentrification?",
                    "options": ["Property value changes due to climate risks", "Urban renewal", "Population growth",
                                "Housing development"],
                    "correct_answer": 0
                },
                {
                    "question": "Which vulnerable group is most affected by climate displacement?",
                    "options": ["Low-income communities", "Wealthy individuals", "Urban professionals",
                                "Tourist populations"],
                    "correct_answer": 0
                }
            ]
        },
        "economic effects": {
            "questions": [
                {
                    "question": "What is the estimated annual global cost of climate change?",
                    "options": ["$500 billion", "$100 billion", "$1 trillion", "$50 billion"],
                    "correct_answer": 0
                },
                {
                    "question": "Which economic sector is most vulnerable to climate change?",
                    "options": ["Agriculture", "Technology", "Entertainment", "Telecommunications"],
                    "correct_answer": 0
                },
                {
                    "question": "What is a carbon tax?",
                    "options": ["Fee on greenhouse gas emissions", "Income tax", "Property tax", "Sales tax"],
                    "correct_answer": 0
                },
                {
                    "question": "How does climate change affect insurance costs?",
                    "options": ["Increases due to higher risk", "Decreases due to competition", "Remains stable",
                                "No significant impact"],
                    "correct_answer": 0
                },
                {
                    "question": "What is green finance?",
                    "options": ["Funding for environmental projects", "Agricultural loans", "Government spending",
                                "Bank investments"],
                    "correct_answer": 0
                },
                {
                    "question": "How do extreme weather events affect GDP?",
                    "options": ["Reduce economic growth", "Increase productivity", "Improve trade", "Boost employment"],
                    "correct_answer": 0
                },
                {
                    "question": "What is climate risk disclosure?",
                    "options": ["Reporting climate-related financial risks", "Weather forecasting",
                                "Environmental regulations", "Carbon emissions data"],
                    "correct_answer": 0
                },
                {
                    "question": "How does climate change affect property values?",
                    "options": ["Decreases in high-risk areas", "Always increases", "No effect",
                                "Only affects commercial property"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the economic impact of sea-level rise?",
                    "options": ["Coastal property damage and loss", "Increased tourism", "Better fishing conditions",
                                "Improved transportation"],
                    "correct_answer": 0
                },
                {
                    "question": "How does climate change affect labor productivity?",
                    "options": ["Reduces due to heat stress", "Increases year-round", "No significant impact",
                                "Only affects indoor work"],
                    "correct_answer": 0
                }
            ]
        },
        "extreme weather": {
            "questions": [
                {
                    "question": "What is the most common extreme weather event?",
                    "options": ["Floods", "Tornadoes", "Hurricanes", "Droughts"],
                    "correct_answer": 0
                },
                {
                    "question": "How does climate change affect hurricane intensity?",
                    "options": ["Increases it", "Decreases it", "No effect", "Only affects duration"],
                    "correct_answer": 0
                },
                {
                    "question": "What is a heat dome?",
                    "options": ["Trapped high pressure system", "Sports stadium", "Weather station",
                                "Temperature measurement device"],
                    "correct_answer": 0
                },
                {
                    "question": "How do extreme weather events affect infrastructure?",
                    "options": ["Damage and disruption", "Improved durability", "No significant impact",
                                "Enhanced performance"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the El Niño effect?",
                    "options": ["Pacific Ocean warming pattern", "Arctic storm system", "Desert wind pattern",
                                "Mountain weather phenomenon"],
                    "correct_answer": 0
                },
                {
                    "question": "How has the frequency of extreme weather events changed?",
                    "options": ["Increased significantly", "Decreased slightly", "Remained the same",
                                "Only seasonal changes"],
                    "correct_answer": 0
                },
                {
                    "question": "What is a flash flood?",
                    "options": ["Rapid flooding from heavy rain", "Coastal flooding", "River overflow",
                                "Groundwater flooding"],
                    "correct_answer": 0
                },
                {
                    "question": "How do extreme weather events affect agriculture?",
                    "options": ["Crop damage and failure", "Improved yields", "No significant impact",
                                "Only affects certain crops"],
                    "correct_answer": 0
                },
                {
                    "question": "What is a polar vortex?",
                    "options": ["Low pressure arctic air system", "Tropical storm", "Desert wind",
                                "Mountain weather pattern"],
                    "correct_answer": 0
                },
                {
                    "question": "How do extreme weather events affect public health?",
                    "options": ["Increased illness and injury", "Improved health conditions", "No significant impact",
                                "Only affects certain groups"],
                    "correct_answer": 0
                }
            ]
        },
        "biodiversity loss": {
            "questions": [
                {
                    "question": "What is the current rate of species extinction?",
                    "options": ["1000 times natural rate", "100 times natural rate", "10 times natural rate",
                                "Same as natural rate"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the main cause of biodiversity loss?",
                    "options": ["Habitat destruction", "Climate change", "Pollution", "Overhunting"],
                    "correct_answer": 0
                },
                {
                    "question": "What is a biodiversity hotspot?",
                    "options": ["Area with many endangered species", "Tourist location", "Wildlife park",
                                "Research station"],
                    "correct_answer": 0
                },
                {
                    "question": "How does biodiversity loss affect ecosystem services?",
                    "options": ["Reduces ecosystem stability", "Improves adaptation", "No significant impact",
                                "Increases resilience"],
                    "correct_answer": 0
                },
                {
                    "question": "What percentage of known species are at risk of extinction?",
                    "options": ["25%", "10%", "50%", "75%"],
                    "correct_answer": 0
                },
                {
                    "question": "What is ecosystem fragmentation?",
                    "options": ["Breaking habitats into smaller parts", "Ecosystem growth", "Species migration",
                                "Habitat improvement"],
                    "correct_answer": 0
                },
                {
                    "question": "How does biodiversity loss affect food security?",
                    "options": ["Reduces crop resilience", "Improves crop yields", "No significant impact",
                                "Only affects wild species"],
                    "correct_answer": 0
                },
                {
                    "question": "What is an invasive species?",
                    "options": ["Non-native harmful species", "Endangered species", "Native species",
                                "Beneficial species"],
                    "correct_answer": 0
                },
                {
                    "question": "How does ocean acidification affect marine biodiversity?",
                    "options": ["Damages coral reefs", "Improves fish populations", "No effect",
                                "Only affects deep ocean"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the Red List?",
                    "options": ["Endangered species inventory", "Conservation area list", "Wildlife protection law",
                                "Species recovery plan"],
                    "correct_answer": 0
                }
            ]
        },
        "air pollution": {
            "questions": [
                {
                    "question": "What is the main source of urban air pollution?",
                    "options": ["Vehicle emissions", "Industrial plants", "Natural sources", "Construction"],
                    "correct_answer": 0
                },
                {
                    "question": "What is PM2.5?",
                    "options": ["Fine particulate matter", "Chemical compound", "Air quality index",
                                "Pollution measurement"],
                    "correct_answer": 0
                },
                {
                    "question": "Which air pollutant is mainly responsible for acid rain?",
                    "options": ["Sulfur dioxide", "Carbon dioxide", "Methane", "Oxygen"],
                    "correct_answer": 0
                },
                {
                    "question": "What is the main health impact of prolonged exposure to fine particulate matter (PM2.5)?",
                    "options": ["Skin irritation", "Respiratory issues", "Eye infections", "Hearing problems"],
                    "correct_answer": 1
                },
                {
                    "question": "Which layer of the atmosphere contains ozone that protects life on Earth from harmful ultraviolet (UV) radiation?",
                    "options": ["Troposphere", "Exosphere", "Mesosphere", "Stratosphere"],
                    "correct_answer": 3
                },
                {
                    "question": "Which of the following is a primary source of indoor air pollution?",
                    "options": ["Forest fires","Traffic emissions", "Tobacco smoke", "Power plants"],
                    "correct_answer": 2
                }
            ]
        }
    }
    if topic in fallback_quizzes:
        # Get all questions for the topic
        all_questions = fallback_quizzes[topic]["questions"]
        # Randomly select 5 questions
        selected_questions = random.sample(all_questions, 5)
        # Return the selected questions in the same format
        return {"questions": selected_questions}


def generate_quiz(topic):
    try:
        # Generate a prompt for the specific topic
        prompt = f"""Generate a quiz about {topic} with 5 multiple-choice questions. 
        Return ONLY a valid JSON object with this structure:
        {{
            "questions": [
                {{
                    "question": "Question text here?",
                    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                    "correct_answer": 0
                }}
            ]
        }}"""

        response = chat_session.send_message(prompt)

        if not response or not response.text:
            # If the response is empty, use a fallback quiz for the specific topic
            app.logger.warning(f"Empty response for {topic}")
            return jsonify(get_fallback_quiz(topic))

        # Try to extract and parse JSON content
        quiz_data = extract_json_content(response.text)

        if quiz_data and "questions" in quiz_data:
            # Validate questions
            valid_questions = []
            for q in quiz_data["questions"]:
                if (isinstance(q, dict) and
                        "question" in q and
                        "options" in q and
                        "correct_answer" in q and
                        isinstance(q["options"], list) and
                        len(q["options"]) == 4):
                    valid_questions.append(q)

            # If we have less than 5 questions, add some from the fallback quiz
            if len(valid_questions) < 5:
                fallback_quiz = get_fallback_quiz(topic)
                for q in fallback_quiz["questions"]:
                    if len(valid_questions) < 5:
                        valid_questions.append(q)
                    else:
                        break

            return jsonify({"questions": valid_questions[:5]})

        # If we couldn't get valid questions, use the fallback quiz for the specific topic
        return jsonify(get_fallback_quiz(topic))

    except Exception as e:
        app.logger.error(f"Quiz generation error: {str(e)}")
        return jsonify(get_fallback_quiz(topic))


# Route handlers
@app.route('/deforestation', methods=['GET'])
def deforestation_quiz():
    return generate_quiz("deforestation")


@app.route('/climate', methods=['GET'])
def climate_quiz():
    return generate_quiz("Climate Change")


@app.route('/Social', methods=['GET'])
def social_quiz():
    return generate_quiz("Social displacement")


@app.route('/EWE', methods=['GET'])
def ewe_quiz():
    return generate_quiz("Extreme Weather")


@app.route('/bio_loss', methods=['GET'])
def bio_loss_quiz():
    return generate_quiz("Biodiversity loss")


@app.route('/air', methods=['GET'])
def air_quiz():
    return generate_quiz("Air Pollution")


@app.route('/EcoEffect', methods=['GET'])
def eco_quiz():
    return generate_quiz("Economic effects")


@app.errorhandler(500)
def handle_500_error(e):
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong. Please try again later."
    }), 500


@app.route('/chatbot', methods=['GET'])
def chatbot_endpoint():
    user_input = request.args.get('message')
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = chat_session.send_message(user_input)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
