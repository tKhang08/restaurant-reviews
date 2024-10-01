from flask import Flask, render_template, request
import pandas as pd
import joblib

app = Flask(__name__)
# Đọc dữ liệu từ CSV
df_restaurants = pd.read_csv('data/restaurant_info_02.csv')
df_reviews = pd.read_csv('data/part-00000-a9ec264d-9f98-4063-9ccc-254507595164-c000.csv')
df_user_reviews = pd.read_csv('data/phan-tich-cam-xuc.csv')

# Kết hợp dữ liệu nhà hàng và đánh giá
df_combined = pd.merge(df_restaurants, df_reviews, on='restaurant_id')

# Gộp thêm dữ liệu từ phan-tich-cam-xuc.csv
df_combined_reviews = pd.merge(df_combined, df_user_reviews, on='restaurant_id', how='left')

# Đọc thêm dữ liệu từ các tệp mới
df_trends = pd.read_csv('data/trend_predictions.csv')
df_ratings = pd.read_csv('data/weighted_avg_ratings.csv')

# Kết hợp dữ liệu dự đoán tình hình và rating hiện tại với df_combined_reviews
df_combined_reviews = pd.merge(df_combined_reviews, df_trends, on='restaurant_id', how='left')
df_combined_reviews = pd.merge(df_combined_reviews, df_ratings, on='restaurant_id', how='left')

# Số lượng nhà hàng hiển thị trên mỗi trang
PER_PAGE = 9

@app.route('/')
def index():
    # Lấy trang hiện tại từ URL, mặc định là 1
    page = request.args.get('page', 1, type=int)

    # Tính toán các nhà hàng cần hiển thị trên trang hiện tại
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    restaurants = df_combined.iloc[start:end].to_dict(orient='records')

    # Tính tổng số trang
    total_pages = (len(df_combined) + PER_PAGE - 1) // PER_PAGE

    return render_template('index.html', restaurants=restaurants, page=page, total_pages=total_pages)

@app.route('/restaurant/<int:restaurant_id>')
def restaurant_detail(restaurant_id):
    # Tìm nhà hàng theo ID
    restaurant = df_combined_reviews[df_combined_reviews['restaurant_id'] == restaurant_id].to_dict(orient='records')

    # Tìm các đánh giá liên quan
    reviews = df_user_reviews[df_user_reviews['restaurant_id'] == restaurant_id].to_dict(orient='records')

    if restaurant:
        restaurant = restaurant[0]  # Lấy nhà hàng đầu tiên (vì to_dict trả về list)
        trend_prediction = restaurant.get('du_doan_tinh_hinh', 'Không có dự đoán')
        current_rating = restaurant.get('rating_hien_tai', 'Chưa có đánh giá')
        return render_template('restaurant_detail.html', 
                               restaurant=restaurant, 
                               reviews=reviews, 
                               trend_prediction=trend_prediction, 
                               current_rating=current_rating)
    else:
        return "Nhà hàng không tồn tại", 404


    
@app.route('/search')
def search():
    query = request.args.get('q', '')  # Lấy từ khóa tìm kiếm từ URL
    if query:
        # Lọc các nhà hàng có tên chứa từ khóa
        filtered_restaurants = df_combined[df_combined['restaurant_name'].str.contains(query, case=False)]
    else:
        filtered_restaurants = df_combined

    restaurants = filtered_restaurants.to_dict(orient='records')
    return render_template('index.html', restaurants=restaurants, page=1, total_pages=1, search_query=query)

from flask import jsonify

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '')
    # Lọc ra các nhà hàng có tên chứa từ khóa tìm kiếm
    suggestions = df_combined[df_combined['restaurant_name'].str.contains(query, case=False)]['restaurant_name'].unique()
    return jsonify(list(suggestions))  # Trả về danh sách gợi ý

if __name__ == '__main__':
    app.run(debug=True)
